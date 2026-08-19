"""规则与 MAD 组合的可解释交易异常识别基线。"""

from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import timedelta

from app.ml.anomaly_config import (
    ANOMALY_LOOKBACK_DAYS,
    COUNTERPARTY_AMOUNT_SHARE,
    MAD_Z_THRESHOLD,
    MISSING_ORDER_LINK_RATIO,
    NIGHT_TRANSACTION_MIN_COUNT,
    NIGHT_TRANSACTION_RATIO,
    RAPID_ROUNDTRIP_AMOUNT_TOLERANCE,
    RAPID_ROUNDTRIP_HOURS,
    REFUND_REVERSAL_RATIO,
    REPEATED_AMOUNT_MIN_COUNT,
    REPEATED_AMOUNT_MIN_VALUE,
    RULE_CONTRIBUTIONS,
)
from app.schemas.anomaly import (
    AnomalyAnalysisRequest,
    AnomalyAnalysisResult,
    AnomalyRuleHit,
    TransactionDetail,
)


def _hit(
    code: str,
    message: str,
    evidence: list[str],
    *,
    level: str = "MEDIUM",
) -> AnomalyRuleHit:
    return AnomalyRuleHit(
        code=code,
        level=level,  # type: ignore[arg-type]
        contribution=RULE_CONTRIBUTIONS[code],
        message=message,
        evidence_transaction_ids=list(dict.fromkeys(evidence))[:20],
    )


def _repeated_amount_hit(transactions: list[TransactionDetail]) -> AnomalyRuleHit | None:
    groups: dict[tuple[object, float], list[TransactionDetail]] = defaultdict(list)
    for item in transactions:
        if (
            item.status == "SUCCESS"
            and item.direction == "IN"
            and item.amount >= REPEATED_AMOUNT_MIN_VALUE
            and item.amount % 100 == 0
        ):
            groups[(item.transaction_time.date(), item.amount)].append(item)
    suspicious = [group for group in groups.values() if len(group) >= REPEATED_AMOUNT_MIN_COUNT]
    if not suspicious:
        return None
    evidence = [item.transaction_id for group in suspicious for item in group]
    return _hit(
        "REPEATED_ROUND_AMOUNT",
        "同日出现多笔相同整数金额入账",
        evidence,
        level="HIGH",
    )


def _off_hours_hit(transactions: list[TransactionDetail]) -> AnomalyRuleHit | None:
    successful = [item for item in transactions if item.status == "SUCCESS"]
    off_hours = [item for item in successful if not item.is_business_hour]
    if not successful:
        return None
    ratio = len(off_hours) / len(successful)
    if len(off_hours) < NIGHT_TRANSACTION_MIN_COUNT or ratio < NIGHT_TRANSACTION_RATIO:
        return None
    return _hit(
        "OFF_HOURS_CONCENTRATION",
        f"非营业时段交易占比达到 {ratio:.1%}",
        [item.transaction_id for item in off_hours],
    )


def _counterparty_hit(transactions: list[TransactionDetail]) -> AnomalyRuleHit | None:
    incoming = [
        item
        for item in transactions
        if item.status == "SUCCESS"
        and item.direction == "IN"
        and item.channel == "COLLECTION"
    ]
    total = sum(item.amount for item in incoming)
    if total <= 0 or len(incoming) < 5:
        return None
    amounts: dict[str, float] = defaultdict(float)
    for item in incoming:
        amounts[item.counterparty_hash] += item.amount
    counterparty, amount = max(amounts.items(), key=lambda pair: pair[1])
    share = amount / total
    if share < COUNTERPARTY_AMOUNT_SHARE:
        return None
    evidence = [
        item.transaction_id for item in incoming if item.counterparty_hash == counterparty
    ]
    return _hit(
        "COUNTERPARTY_CONCENTRATION",
        f"单一对手方入账金额占比达到 {share:.1%}",
        evidence,
        level="HIGH",
    )


def _rapid_roundtrip_hit(transactions: list[TransactionDetail]) -> AnomalyRuleHit | None:
    ordered = sorted(transactions, key=lambda item: item.transaction_time)
    evidence: list[str] = []
    for index, incoming in enumerate(ordered):
        if incoming.status != "SUCCESS" or incoming.direction != "IN":
            continue
        for outgoing in ordered[index + 1 :]:
            elapsed = outgoing.transaction_time - incoming.transaction_time
            if elapsed > timedelta(hours=RAPID_ROUNDTRIP_HOURS):
                break
            if outgoing.status != "SUCCESS" or outgoing.direction != "OUT":
                continue
            difference = abs(outgoing.amount - incoming.amount) / incoming.amount
            if difference <= RAPID_ROUNDTRIP_AMOUNT_TOLERANCE:
                evidence.extend([incoming.transaction_id, outgoing.transaction_id])
    if not evidence:
        return None
    return _hit(
        "RAPID_IN_OUT_ROUNDTRIP",
        "发现入账后短时间内近等额转出",
        evidence,
        level="HIGH",
    )


def _refund_hit(transactions: list[TransactionDetail]) -> AnomalyRuleHit | None:
    refund_items = [
        item
        for item in transactions
        if item.channel in {"REFUND", "REVERSAL"}
        or item.status in {"REFUNDED", "REVERSED"}
    ]
    if not transactions:
        return None
    ratio = len(refund_items) / len(transactions)
    if ratio < REFUND_REVERSAL_RATIO:
        return None
    return _hit(
        "HIGH_REFUND_REVERSAL",
        f"退款、撤销或冲正交易占比达到 {ratio:.1%}",
        [item.transaction_id for item in refund_items],
    )


def _mad_hit(transactions: list[TransactionDetail]) -> AnomalyRuleHit | None:
    incoming = [
        item
        for item in transactions
        if item.status == "SUCCESS" and item.direction == "IN"
    ]
    if len(incoming) < 7:
        return None
    amounts = [item.amount for item in incoming]
    median = statistics.median(amounts)
    mad = statistics.median(abs(amount - median) for amount in amounts)
    if mad == 0:
        return None
    evidence = [
        item.transaction_id
        for item in incoming
        if 0.6745 * abs(item.amount - median) / mad > MAD_Z_THRESHOLD
    ]
    if not evidence:
        return None
    return _hit(
        "AMOUNT_MAD_OUTLIER",
        "交易金额相对同商户近期分布出现 MAD 稳健离群",
        evidence,
    )


def _missing_order_hit(transactions: list[TransactionDetail]) -> AnomalyRuleHit | None:
    collections = [
        item
        for item in transactions
        if item.status == "SUCCESS"
        and item.direction == "IN"
        and item.channel == "COLLECTION"
    ]
    missing = [item for item in collections if not item.order_id_hash]
    if len(collections) < 5:
        return None
    ratio = len(missing) / len(collections)
    if ratio < MISSING_ORDER_LINK_RATIO:
        return None
    return _hit(
        "MISSING_ORDER_LINK",
        f"收款交易缺少平台订单关联的占比达到 {ratio:.1%}",
        [item.transaction_id for item in missing],
    )


def analyze_transactions(request: AnomalyAnalysisRequest) -> AnomalyAnalysisResult:
    evaluated_at = request.as_of_time or max(
        item.transaction_time for item in request.transactions
    )
    cutoff = evaluated_at - timedelta(days=ANOMALY_LOOKBACK_DAYS)
    recent = [
        item
        for item in request.transactions
        if cutoff <= item.transaction_time <= evaluated_at
    ]

    detectors = (
        _repeated_amount_hit,
        _off_hours_hit,
        _counterparty_hit,
        _rapid_roundtrip_hit,
        _refund_hit,
        _mad_hit,
        _missing_order_hit,
    )
    hits = [hit for detector in detectors if (hit := detector(recent)) is not None]
    score = min(100, sum(hit.contribution for hit in hits))
    risk_level = "HIGH" if score >= 60 else "MEDIUM" if score >= 20 else "LOW"
    confidence = "HIGH" if len(recent) >= 30 else "MEDIUM" if len(recent) >= 10 else "LOW"
    evidence = list(
        dict.fromkeys(
            transaction_id
            for hit in hits
            for transaction_id in hit.evidence_transaction_ids
        )
    )

    return AnomalyAnalysisResult(
        merchant_id=request.merchant_id,
        evaluated_at=evaluated_at,
        transaction_count=len(request.transactions),
        recent_transaction_count=len(recent),
        anomaly_score=score,
        risk_level=risk_level,  # type: ignore[arg-type]
        confidence=confidence,  # type: ignore[arg-type]
        reason_codes=[hit.code for hit in hits],
        rule_hits=hits,
        evidence_transaction_ids=evidence[:50],
    )
