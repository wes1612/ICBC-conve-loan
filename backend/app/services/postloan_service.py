"""确定性贷后演示轨迹、三引擎月度复评与动态额度状态机。"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from threading import RLock
from typing import Any

from app.ml.anomaly_engine import analyze_transactions
from app.ml.cash_gap_engine import forecast_cash_gap
from app.schemas.anomaly import AnomalyAnalysisRequest, TransactionDetail
from app.schemas.cash_gap import CashGapForecastRequest, MonthlyCashflow
from app.schemas.demo import DemoMerchantId
from app.schemas.merchant import MerchantAnalysisRequest
from app.schemas.postloan import (
    CreditReviewResult,
    LoanAccountSnapshot,
    MerchantSubmission,
    MerchantSubmissionRequest,
    MonthlyOperatingMetrics,
    PostLoanAlert,
    PostLoanModelSnapshot,
    PostLoanMonthlySnapshot,
    PostLoanSourceStatus,
    PostLoanTimeline,
    RepaymentPerformance,
    ReviewDecisionRequest,
    SourceAuthorizationRequest,
)
from app.services.analysis_service import analyze_merchant
from app.services.demo_service import DEMO_IDS, get_demo_case


POLICY_VERSION = "postloan_competition_policy_v1"
START_MONTH = date(2026, 8, 1)


SCENARIOS: dict[DemoMerchantId, dict[str, Any]] = {
    "M001": {
        "name": "稳定经营、连续履约",
        "description": "经营稳步增长且按期还款，连续良好后触发小幅提额建议。",
        "initial_limit": 320_000,
    },
    "M002": {
        "name": "快速成长、资金需求上升",
        "description": "订单与流水快速增长、额度使用合理，分阶段产生提额建议。",
        "initial_limit": 180_000,
    },
    "M003": {
        "name": "经营恶化、还款承压",
        "description": "流水持续下滑、退款与逾期上升，先降额后冻结新增提款。",
        "initial_limit": 160_000,
    },
    "M004": {
        "name": "外部授权到期、数据缺失",
        "description": "经营相对稳定但平台授权到期，系统维持额度并转人工补充核验。",
        "initial_limit": 100_000,
    },
    "M005": {
        "name": "异常交易持续暴露",
        "description": "贷后交易出现回流与订单关联异常，立即冻结新增提款并人工调查。",
        "initial_limit": 120_000,
    },
}


@dataclass(frozen=True)
class TrajectoryPoint:
    receipt_factor: float
    order_factor: float
    refund_rate: float
    complaints: int
    days_past_due: int
    utilization: float
    compliant_use_ratio: float
    cash_balance: float
    outflow_ratio: float
    anomaly_mode: str = "NORMAL"


def _month(value: date, offset: int) -> date:
    month_index = value.year * 12 + value.month - 1 + offset
    return date(month_index // 12, month_index % 12 + 1, 1)


def _month_end(value: date) -> date:
    return date(value.year, value.month, calendar.monthrange(value.year, value.month)[1])


def _trajectory_point(merchant_id: DemoMerchantId, index: int) -> TrajectoryPoint:
    """返回五类固定情景中的第 index 个月，所有数值均为竞赛模拟参数。"""

    if merchant_id == "M001":
        return TrajectoryPoint(
            receipt_factor=1.02 + index * 0.018,
            order_factor=1.01 + index * 0.016,
            refund_rate=max(0.018, 0.026 - index * 0.0005),
            complaints=0 if index % 4 else 1,
            days_past_due=0,
            utilization=min(0.82, 0.62 + index * 0.015),
            compliant_use_ratio=0.98,
            cash_balance=165_000 + index * 8_000,
            outflow_ratio=0.69,
        )
    if merchant_id == "M002":
        return TrajectoryPoint(
            receipt_factor=1.05 + index * 0.045,
            order_factor=1.06 + index * 0.05,
            refund_rate=max(0.025, 0.041 - index * 0.001),
            complaints=1 if index % 3 == 0 else 0,
            days_past_due=0,
            utilization=min(0.91, 0.70 + index * 0.018),
            compliant_use_ratio=0.96,
            cash_balance=92_000 + index * 7_500,
            outflow_ratio=0.76,
        )
    if merchant_id == "M003":
        overdue_path = (0, 0, 2, 5, 8, 12, 18, 23, 30, 35, 42, 50)
        factor = max(0.42, 1.0 - index * 0.065)
        return TrajectoryPoint(
            receipt_factor=factor,
            order_factor=max(0.45, factor - 0.03),
            refund_rate=min(0.24, 0.07 + index * 0.014),
            complaints=2 + index // 2,
            days_past_due=overdue_path[index],
            utilization=min(0.96, 0.76 + index * 0.018),
            compliant_use_ratio=max(0.80, 0.96 - index * 0.012),
            cash_balance=max(8_000, 72_000 - index * 6_000),
            outflow_ratio=min(1.12, 0.88 + index * 0.025),
            anomaly_mode="REFUND" if index >= 4 else "NORMAL",
        )
    if merchant_id == "M004":
        return TrajectoryPoint(
            receipt_factor=1.0 + index * 0.004,
            order_factor=1.0 + index * 0.003,
            refund_rate=0.065,
            complaints=1,
            days_past_due=0,
            utilization=0.48,
            compliant_use_ratio=0.95,
            cash_balance=105_000 + index * 800,
            outflow_ratio=0.78,
            anomaly_mode="MISSING_LINK" if index >= 2 else "NORMAL",
        )
    return TrajectoryPoint(
        receipt_factor=max(0.82, 1.02 - index * 0.018),
        order_factor=max(0.78, 1.0 - index * 0.022),
        refund_rate=min(0.18, 0.07 + index * 0.009),
        complaints=1 + index // 3,
        days_past_due=0 if index < 4 else min(20, (index - 3) * 3),
        utilization=0.86,
        compliant_use_ratio=max(0.62, 0.78 - index * 0.018),
        cash_balance=max(28_000, 95_000 - index * 4_500),
        outflow_ratio=0.83,
        anomaly_mode="HIGH_RISK",
    )


def _monthly_merchant(
    merchant_id: DemoMerchantId,
    index: int,
    point: TrajectoryPoint,
) -> MerchantAnalysisRequest:
    raw = get_demo_case(merchant_id).merchant.model_dump()
    structural = raw["structural"]
    baseline_receipt = structural["monthly_receipts"][-1]
    baseline_orders = structural["monthly_orders"][-1]
    prior_redemption = structural["monthly_redemption_rates"][-1]
    # 逐月滚动序列，确保第 N 月评分只使用申请前历史和已经发生的 1..N 月。
    for previous_index in range(index + 1):
        previous = _trajectory_point(merchant_id, previous_index)
        receipt = round(baseline_receipt * previous.receipt_factor, 2)
        orders = round(baseline_orders * previous.order_factor)
        structural["monthly_receipts"] = structural["monthly_receipts"][1:] + [receipt]
        structural["monthly_orders"] = structural["monthly_orders"][1:] + [orders]
        structural["monthly_refund_rates"] = structural["monthly_refund_rates"][1:] + [
            previous.refund_rate
        ]
        structural["monthly_redemption_rates"] = structural["monthly_redemption_rates"][1:] + [
            prior_redemption
        ]
    recent_receipts = structural["monthly_receipts"][-6:]
    structural["operating_cash_inflow_6m"] = round(sum(recent_receipts) * 0.97, 2)
    structural["operating_cash_outflow_6m"] = round(
        sum(recent_receipts) * point.outflow_ratio,
        2,
    )
    structural["transaction_anomaly_hits"] = 1 if point.anomaly_mode == "HIGH_RISK" else 0
    if merchant_id == "M004" and index >= 2:
        structural["missing_key_field_count"] = max(6, structural["missing_key_field_count"])
    unstructured = raw["unstructured"]
    unstructured["complaint_count_6m"] = point.complaints
    unstructured["negative_review_ratio"] = min(
        0.5,
        max(float(unstructured.get("negative_review_ratio") or 0), point.refund_rate * 1.25),
    )
    return MerchantAnalysisRequest.model_validate(raw)


def _monthly_transactions(
    merchant_id: DemoMerchantId,
    month_value: date,
    point: TrajectoryPoint,
) -> AnomalyAnalysisRequest:
    transactions: list[TransactionDetail] = []
    for position in range(24):
        day = 2 + position % 24
        transactions.append(
            TransactionDetail(
                merchant_id=merchant_id,
                transaction_id=f"PL-{merchant_id}-{month_value:%Y%m}-{position + 1:03d}",
                transaction_time=datetime(
                    month_value.year,
                    month_value.month,
                    day,
                    9 + position % 9,
                    10,
                    tzinfo=timezone.utc,
                ),
                direction="IN",
                amount=round(860 + position * 71 + (index_seed(merchant_id) * 13), 2),
                counterparty_hash=f"PL-CP-{merchant_id}-{position:02d}",
                channel="COLLECTION",
                status="SUCCESS",
                order_id_hash=(
                    None
                    if point.anomaly_mode == "MISSING_LINK" and position < 10
                    else f"PL-ORDER-{merchant_id}-{month_value:%Y%m}-{position:02d}"
                ),
                invoice_id_hash=f"PL-INV-{merchant_id}-{month_value:%Y%m}-{position:02d}",
                purpose_code="OPERATING",
                is_business_hour=True,
            )
        )

    if point.anomaly_mode == "REFUND":
        for position in range(6):
            transactions.append(
                TransactionDetail(
                    merchant_id=merchant_id,
                    transaction_id=f"PL-{merchant_id}-{month_value:%Y%m}-R{position + 1:02d}",
                    transaction_time=datetime(
                        month_value.year,
                        month_value.month,
                        20 + position,
                        15,
                        tzinfo=timezone.utc,
                    ),
                    direction="OUT",
                    amount=1800 + position * 80,
                    counterparty_hash=f"PL-REFUND-{position:02d}",
                    channel="REFUND",
                    status="SUCCESS",
                    order_id_hash=f"PL-REFUND-ORDER-{position:02d}",
                    purpose_code="CUSTOMER_REFUND",
                    is_business_hour=True,
                )
            )
    elif point.anomaly_mode == "HIGH_RISK":
        anomaly_day = min(26, 18 + month_value.month % 5)
        for position in range(3):
            transactions.append(
                TransactionDetail(
                    merchant_id=merchant_id,
                    transaction_id=f"PL-{merchant_id}-{month_value:%Y%m}-A{position + 1}",
                    transaction_time=datetime(
                        month_value.year,
                        month_value.month,
                        anomaly_day,
                        20,
                        position * 5,
                        tzinfo=timezone.utc,
                    ),
                    direction="IN",
                    amount=5000,
                    counterparty_hash="PL-SUSPICIOUS-CP",
                    channel="COLLECTION",
                    status="SUCCESS",
                    order_id_hash=None,
                    purpose_code="UNKNOWN",
                    is_business_hour=False,
                )
            )
        transactions.extend(
            [
                TransactionDetail(
                    merchant_id=merchant_id,
                    transaction_id=f"PL-{merchant_id}-{month_value:%Y%m}-RT-IN",
                    transaction_time=datetime(
                        month_value.year,
                        month_value.month,
                        anomaly_day + 1,
                        21,
                        tzinfo=timezone.utc,
                    ),
                    direction="IN",
                    amount=12_000,
                    counterparty_hash="PL-SUSPICIOUS-CP",
                    channel="COLLECTION",
                    status="SUCCESS",
                    order_id_hash=None,
                    purpose_code="UNKNOWN",
                    is_business_hour=False,
                ),
                TransactionDetail(
                    merchant_id=merchant_id,
                    transaction_id=f"PL-{merchant_id}-{month_value:%Y%m}-RT-OUT",
                    transaction_time=datetime(
                        month_value.year,
                        month_value.month,
                        anomaly_day + 1,
                        21,
                        40,
                        tzinfo=timezone.utc,
                    ),
                    direction="OUT",
                    amount=11_850,
                    counterparty_hash="PL-SUSPICIOUS-OUT",
                    channel="TRANSFER",
                    status="SUCCESS",
                    order_id_hash=None,
                    purpose_code="UNKNOWN",
                    is_business_hour=False,
                ),
            ]
        )

    return AnomalyAnalysisRequest(
        merchant_id=merchant_id,
        as_of_time=datetime.combine(_month_end(month_value), datetime.max.time(), timezone.utc),
        transactions=transactions,
    )


def index_seed(merchant_id: DemoMerchantId) -> int:
    return int(merchant_id[-1])


def _monthly_cash_gap(
    merchant_id: DemoMerchantId,
    month_value: date,
    point: TrajectoryPoint,
    visible_points: list[TrajectoryPoint],
    current_limit: float,
    outstanding: float,
) -> CashGapForecastRequest:
    base = get_demo_case(merchant_id).cash_gap.model_dump()
    history = [MonthlyCashflow.model_validate(item) for item in base["history"]]
    baseline_receipt = get_demo_case(merchant_id).merchant.structural.monthly_receipts[-1]
    for offset, previous in enumerate(visible_points):
        history.append(
            MonthlyCashflow(
                month=_month(START_MONTH, offset),
                operating_inflow=round(baseline_receipt * previous.receipt_factor * 0.97, 2),
                operating_outflow=round(
                    baseline_receipt
                    * previous.receipt_factor
                    * previous.outflow_ratio,
                    2,
                ),
            )
        )
    planned_capex = base["planned_capex_3m"]
    if merchant_id == "M002":
        # 快速成长情景保留扩店需求，但避免把计划开支直接等同于流动性危机。
        planned_capex = [30_000, 40_000, 0]
    return CashGapForecastRequest(
        merchant_id=merchant_id,
        snapshot_date=_month_end(month_value),
        history=history,
        current_cash_balance=point.cash_balance,
        restricted_cash=min(float(base["restricted_cash"]), point.cash_balance * 0.2),
        unused_credit=max(0, current_limit - outstanding),
        minimum_cash_balance=float(base["minimum_cash_balance"]),
        planned_capex_3m=planned_capex,
        debt_service_3m=base["debt_service_3m"],
        confirmed_extra_inflows_3m=base["confirmed_extra_inflows_3m"],
        stress_inflow_decline=base["stress_inflow_decline"],
        stress_outflow_increase=base["stress_outflow_increase"],
    )


def _round_limit(value: float) -> float:
    return float(max(0, round(value / 1000) * 1000))


def _review_result(
    merchant_id: DemoMerchantId,
    month_value: date,
    current_limit: float,
    outstanding: float,
    operating: MonthlyOperatingMetrics,
    repayment: RepaymentPerformance,
    models: PostLoanModelSnapshot,
    data_quality: str,
    history: list[PostLoanMonthlySnapshot],
    candidate_limit: float,
    last_change_index: int | None,
) -> CreditReviewResult:
    action = "MAINTAIN"
    alert_level = "LOW"
    reasons = ["本月经营、履约和资金表现未触发额度调整门槛"]
    reason_codes = ["PERFORMANCE_WITHIN_POLICY"]
    status = "AUTO_APPLIED"
    proposed = current_limit

    if (
        models.anomaly_risk == "HIGH"
        or repayment.days_past_due >= 15
        or operating.compliant_use_ratio < 0.75
    ):
        action = "FREEZE"
        alert_level = "HIGH"
        status = "AUTO_APPLIED"
        reason_codes = []
        reasons = []
        if models.anomaly_risk == "HIGH":
            reason_codes.append("HIGH_RISK_ANOMALY")
            reasons.append("异常交易模型识别到高风险资金回流或关联缺失")
        if repayment.days_past_due >= 15:
            reason_codes.append("SEVERE_OVERDUE")
            reasons.append(f"本期逾期 {repayment.days_past_due} 天，达到冻结新增提款阈值")
        if operating.compliant_use_ratio < 0.75:
            reason_codes.append("PURPOSE_COMPLIANCE_RISK")
            reasons.append("模拟资金用途合规比例低于竞赛政策阈值")
    elif data_quality in {"MISSING", "CONFLICT"} or models.confidence == "LOW":
        action = "MANUAL_REVIEW"
        alert_level = "MEDIUM"
        status = "PENDING_REVIEW"
        reason_codes = ["DATA_QUALITY_GATE"]
        reasons = ["平台授权、资料完整性或主体一致性不足，模型结果不自动调整额度"]
    else:
        recent_receipts = [item.operating.receipts for item in history[-2:]] + [
            operating.receipts
        ]
        two_month_decline = (
            len(recent_receipts) >= 3
            and recent_receipts[-1] < recent_receipts[-3] * 0.90
        )
        deterioration = (
            repayment.days_past_due >= 5
            or operating.refund_rate >= 0.12
            or models.cash_gap_risk == "HIGH"
            or two_month_decline
        )
        if deterioration:
            action = "DECREASE"
            alert_level = "MEDIUM"
            status = "PENDING_REVIEW"
            proposed = _round_limit(max(outstanding, current_limit * 0.90))
            reason_codes = []
            reasons = []
            if repayment.days_past_due >= 5:
                reason_codes.append("REPAYMENT_PRESSURE")
                reasons.append(f"本期还款逾期 {repayment.days_past_due} 天")
            if operating.refund_rate >= 0.12:
                reason_codes.append("REFUND_RATE_RISING")
                reasons.append(f"退款率升至 {operating.refund_rate:.1%}")
            if models.cash_gap_risk == "HIGH":
                reason_codes.append("CASH_GAP_HIGH")
                reasons.append("三个月压力情景出现较高资金缺口")
            if two_month_decline:
                reason_codes.append("RECEIPT_DECLINE_2M")
                reasons.append("近两个月经营流水累计下降超过竞赛政策阈值")
        else:
            good_months = history[-2:] if len(history) >= 2 else []
            three_good = len(good_months) == 2 and all(
                item.repayment.days_past_due == 0
                and item.models.anomaly_risk == "LOW"
                and item.operating.compliant_use_ratio >= 0.90
                for item in good_months
            ) and repayment.days_past_due == 0 and models.anomaly_risk == "LOW"
            growth = (
                operating.receipts / good_months[0].operating.receipts - 1
                if good_months
                else 0
            )
            average_utilization = (
                sum(item.operating.limit_utilization for item in good_months)
                + operating.limit_utilization
            ) / 3 if good_months else 0
            cooldown_ok = last_change_index is None or len(history) - last_change_index >= 3
            if (
                three_good
                and growth >= 0.03
                and 0.55 <= average_utilization <= 0.95
                and candidate_limit >= current_limit * 1.05
                and models.cash_gap_risk != "HIGH"
                and cooldown_ok
            ):
                action = "INCREASE"
                alert_level = "LOW"
                status = "PENDING_REVIEW"
                proposed = _round_limit(
                    min(candidate_limit, current_limit * 1.15)
                )
                reason_codes = [
                    "REPAYMENT_GOOD_3M",
                    "RECEIPT_GROWTH_STABLE",
                    "LIMIT_UTILIZATION_HEALTHY",
                    "NO_HIGH_RISK_ANOMALY",
                ]
                reasons = [
                    "连续三个月按期还款",
                    f"三个月经营流水增长 {growth:.1%}",
                    f"平均额度使用率 {average_utilization:.1%}，存在真实资金需求",
                    "未发现高风险异常交易或高资金缺口",
                ]

    next_review = _month(month_value, 1)
    return CreditReviewResult(
        review_id=f"PLR-{merchant_id}-{month_value:%Y%m}",
        review_month=month_value,
        action=action,  # type: ignore[arg-type]
        current_limit=current_limit,
        candidate_limit=max(outstanding, candidate_limit),
        proposed_limit=max(outstanding, proposed),
        outstanding_principal=outstanding,
        alert_level=alert_level,  # type: ignore[arg-type]
        reason_codes=reason_codes,
        reasons=reasons,
        status=status,  # type: ignore[arg-type]
        next_review_date=next_review,
        policy_version=POLICY_VERSION,
    )


def _seed_submissions(merchant_id: DemoMerchantId) -> list[MerchantSubmission]:
    if merchant_id not in {"M003", "M004"}:
        return []
    descriptions = {
        "M003": "商户说明近期退款上升来自门店装修停业，并补充主要采购合同。",
        "M004": "商户补充最近一个月他行结算流水，等待客户经理交叉核验。",
    }
    categories = {"M003": "EXPLANATION", "M004": "OFF_BANK_STATEMENT"}
    return [
        MerchantSubmission(
            submission_id=f"SUB-{merchant_id}-SEED",
            merchant_id=merchant_id,
            category=categories[merchant_id],  # type: ignore[arg-type]
            description=descriptions[merchant_id],
            file_name=f"{merchant_id}_贷后补充材料_模拟.pdf",
            submitted_at=datetime(2026, 8, 15, 10, tzinfo=timezone.utc),
        )
    ]


class PostLoanService:
    """进程内演示仓库；重启后恢复确定性初始状态。"""

    def __init__(self) -> None:
        self._lock = RLock()
        self._state: dict[DemoMerchantId, dict[str, Any]] = {}
        self.reset_all()

    def reset_all(self) -> None:
        with self._lock:
            self._state = {
                merchant_id: {
                    "month_index": 1,
                    "decisions": {},
                    "authorizations": {},
                    "submissions": _seed_submissions(merchant_id),
                }
                for merchant_id in DEMO_IDS
            }

    def reset(self, merchant_id: DemoMerchantId) -> PostLoanTimeline:
        with self._lock:
            self._state[merchant_id] = {
                "month_index": 1,
                "decisions": {},
                "authorizations": {},
                "submissions": _seed_submissions(merchant_id),
            }
            return self._build_timeline(merchant_id)

    def timeline(self, merchant_id: DemoMerchantId) -> PostLoanTimeline:
        with self._lock:
            return self._build_timeline(merchant_id)

    def advance(self, merchant_id: DemoMerchantId) -> PostLoanTimeline:
        with self._lock:
            state = self._state[merchant_id]
            state["month_index"] = min(12, state["month_index"] + 1)
            return self._build_timeline(merchant_id)

    def submit(
        self,
        merchant_id: DemoMerchantId,
        request: MerchantSubmissionRequest,
    ) -> PostLoanTimeline:
        with self._lock:
            submissions: list[MerchantSubmission] = self._state[merchant_id]["submissions"]
            submissions.append(
                MerchantSubmission(
                    submission_id=f"SUB-{merchant_id}-{len(submissions) + 1:03d}",
                    merchant_id=merchant_id,
                    category=request.category,
                    description=request.description,
                    file_name=request.file_name,
                    submitted_at=datetime.now(timezone.utc),
                )
            )
            return self._build_timeline(merchant_id)

    def authorize(
        self,
        merchant_id: DemoMerchantId,
        source_id: str,
        request: SourceAuthorizationRequest,
    ) -> PostLoanTimeline:
        if source_id not in {"platform_meituan", "enterprise_registry"}:
            raise ValueError("只有外部授权数据源可以续期或撤销")
        with self._lock:
            self._state[merchant_id]["authorizations"][source_id] = {
                "status": "ACTIVE" if request.action == "RENEW" else "REVOKED",
                "expires_at": request.expires_at,
            }
            return self._build_timeline(merchant_id)

    def decide(
        self,
        review_id: str,
        request: ReviewDecisionRequest,
    ) -> PostLoanTimeline:
        parts = review_id.split("-")
        if len(parts) != 3 or parts[0] != "PLR" or parts[1] not in DEMO_IDS:
            raise ValueError("review_id 不存在")
        merchant_id: DemoMerchantId = parts[1]  # type: ignore[assignment]
        with self._lock:
            timeline = self._build_timeline(merchant_id)
            review = next(
                (item.review for item in timeline.snapshots if item.review.review_id == review_id),
                None,
            )
            if review is None:
                raise ValueError("只能处理已经生成的月度复评")
            if request.decision == "APPROVE":
                approved_limit = request.approved_limit or review.proposed_limit
                if approved_limit < review.outstanding_principal:
                    raise ValueError("批准额度不能低于未偿本金")
                if approved_limit > review.current_limit * 1.15 and review.action == "INCREASE":
                    raise ValueError("单次提额不能超过当前额度的 15%")
            self._state[merchant_id]["decisions"][review_id] = request.model_dump()
            return self._build_timeline(merchant_id)

    def alerts(self) -> list[PostLoanAlert]:
        with self._lock:
            return [
                alert
                for merchant_id in DEMO_IDS
                for alert in self._build_timeline(merchant_id).alerts
            ]

    def _source_statuses(
        self,
        merchant_id: DemoMerchantId,
        current_index: int,
    ) -> list[PostLoanSourceStatus]:
        state = self._state[merchant_id]
        current_month = _month(START_MONTH, current_index - 1)
        observed = datetime.combine(_month_end(current_month), datetime.min.time(), timezone.utc)
        overrides = state["authorizations"]
        platform_expired = merchant_id == "M004" and current_index >= 3
        platform_status = "EXPIRED" if platform_expired else "ACTIVE"
        platform_expires = date(2026, 9, 30) if platform_expired else date(2027, 8, 31)
        if override := overrides.get("platform_meituan"):
            platform_status = override["status"]
            platform_expires = override["expires_at"]
        platform_missing = platform_status != "ACTIVE"
        submissions: list[MerchantSubmission] = state["submissions"]
        return [
            PostLoanSourceStatus(
                source_id="bank_core",
                display_name="工行信贷与还款系统",
                source_type="BANK_INTERNAL_SIMULATED",
                authorization_status="NOT_REQUIRED",
                scopes=["贷款余额", "提款", "还款", "逾期"],
                last_synced_at=observed,
                freshness_hours=1,
                quality_status="VERIFIED",
                verified=True,
                record_count=current_index * 4,
            ),
            PostLoanSourceStatus(
                source_id="icbc_settlement",
                display_name="工行经营回款账户",
                source_type="BANK_INTERNAL_SIMULATED",
                authorization_status="NOT_REQUIRED",
                scopes=["经营流水", "资金流向", "异常交易"],
                last_synced_at=observed,
                freshness_hours=24,
                quality_status="VERIFIED",
                verified=True,
                record_count=current_index * 30,
            ),
            PostLoanSourceStatus(
                source_id="platform_meituan",
                display_name="经营平台订单接口",
                source_type="PLATFORM_AUTHORIZED_SIMULATED",
                authorization_status=platform_status,  # type: ignore[arg-type]
                scopes=["订单", "退款", "核销", "评价"],
                last_synced_at=None if platform_missing else observed - timedelta(hours=8),
                expires_at=platform_expires,
                freshness_hours=None if platform_missing else 8,
                quality_status="MISSING" if platform_missing else "VERIFIED",
                verified=not platform_missing,
                record_count=0 if platform_missing else current_index * 25,
            ),
            PostLoanSourceStatus(
                source_id="merchant_supplement",
                display_name="商户补充材料",
                source_type="MERCHANT_SUBMITTED_SIMULATED",
                authorization_status="NOT_REQUIRED",
                scopes=["他行流水", "合同", "资金用途证明", "异常说明"],
                last_synced_at=submissions[-1].submitted_at if submissions else None,
                quality_status="REPORTED",
                verified=False,
                record_count=len(submissions),
            ),
            PostLoanSourceStatus(
                source_id="manual_verification",
                display_name="客户经理人工核验",
                source_type="MANUAL_VERIFIED_SIMULATED",
                authorization_status="NOT_REQUIRED",
                scopes=["材料交叉核验", "电话回访", "现场检查"],
                last_synced_at=None,
                quality_status="VERIFIED",
                verified=True,
                record_count=len(state["decisions"]),
            ),
        ]

    def _build_timeline(self, merchant_id: DemoMerchantId) -> PostLoanTimeline:
        state = self._state[merchant_id]
        visible_count: int = state["month_index"]
        source_statuses = self._source_statuses(merchant_id, visible_count)
        platform_override = state["authorizations"].get("platform_meituan")
        scenario = SCENARIOS[merchant_id]
        initial_limit = float(scenario["initial_limit"])
        current_limit = initial_limit
        frozen = False
        last_change_index: int | None = None
        snapshots: list[PostLoanMonthlySnapshot] = []
        alerts: list[PostLoanAlert] = []
        points: list[TrajectoryPoint] = []

        for index in range(visible_count):
            month_value = _month(START_MONTH, index)
            point = _trajectory_point(merchant_id, index)
            points.append(point)
            platform_active_for_month = (
                bool(platform_override and platform_override["status"] == "ACTIVE")
                or not (merchant_id == "M004" and index >= 2)
            )
            outstanding = _round_limit(current_limit * point.utilization)
            scheduled = _round_limit(max(3_000, initial_limit * 0.025))
            paid = scheduled if point.days_past_due < 15 else _round_limit(scheduled * 0.5)
            due_date = date(month_value.year, month_value.month, 5)
            scheduled_payment_date = due_date + timedelta(days=point.days_past_due)
            payment_date = (
                scheduled_payment_date
                if scheduled_payment_date <= _month_end(month_value)
                else None
            )
            if payment_date is None:
                paid = 0
            repayment = RepaymentPerformance(
                due_date=due_date,
                scheduled_amount=scheduled,
                paid_amount=paid,
                payment_date=payment_date,
                days_past_due=point.days_past_due,
                on_time=point.days_past_due == 0,
            )
            base_receipt = get_demo_case(merchant_id).merchant.structural.monthly_receipts[-1]
            receipts = round(base_receipt * point.receipt_factor, 2)
            previous_receipts = snapshots[-1].operating.receipts if snapshots else base_receipt
            operating = MonthlyOperatingMetrics(
                receipts=receipts,
                receipt_mom_growth=round(receipts / previous_receipts - 1, 4),
                orders=round(
                    get_demo_case(merchant_id).merchant.structural.monthly_orders[-1]
                    * point.order_factor
                ),
                refund_rate=point.refund_rate,
                complaint_count=point.complaints,
                cash_balance=point.cash_balance,
                limit_utilization=point.utilization,
                compliant_use_ratio=point.compliant_use_ratio,
            )
            score = analyze_merchant(_monthly_merchant(merchant_id, index, point))
            anomaly = analyze_transactions(
                _monthly_transactions(merchant_id, month_value, point)
            )
            cash_gap = forecast_cash_gap(
                _monthly_cash_gap(
                    merchant_id,
                    month_value,
                    point,
                    points,
                    current_limit,
                    outstanding,
                )
            )
            data_quality = (
                "MISSING"
                if merchant_id == "M004" and index >= 2 and not platform_active_for_month
                else "CONFLICT"
                if merchant_id == "M005"
                else "VERIFIED"
            )
            confidence = (
                "LOW"
                if data_quality == "MISSING"
                else "MEDIUM"
                if merchant_id == "M004" and platform_active_for_month
                else score.confidence
            )
            models = PostLoanModelSnapshot(
                operating_credit_score=score.operating_credit_score,
                credit_grade=score.credit_grade,
                anomaly_score=anomaly.anomaly_score,
                anomaly_risk=anomaly.risk_level,
                max_p90_funding_gap=cash_gap.max_p90_funding_gap,
                cash_gap_risk=cash_gap.risk_level,
                confidence=confidence,  # type: ignore[arg-type]
                score_model_version=score.score_version,
                anomaly_model_version=anomaly.model_version,
                cash_gap_model_version=cash_gap.model_version,
            )
            candidate = _round_limit(score.limit.recommended_limit)
            review = _review_result(
                merchant_id,
                month_value,
                current_limit,
                outstanding,
                operating,
                repayment,
                models,
                data_quality,
                snapshots,
                candidate,
                last_change_index,
            )

            if decision := state["decisions"].get(review.review_id):
                review.reviewer_note = decision.get("note")
                if decision["decision"] == "APPROVE":
                    review.status = "APPROVED"
                    approved_limit = float(decision.get("approved_limit") or review.proposed_limit)
                    if approved_limit != current_limit:
                        current_limit = approved_limit
                        last_change_index = index
                elif decision["decision"] == "MAINTAIN":
                    review.status = "REJECTED"
                else:
                    review.status = "PENDING_REVIEW"

            if review.action == "FREEZE":
                frozen = True

            observed_at = datetime.combine(due_date, datetime.min.time(), timezone.utc)
            snapshot = PostLoanMonthlySnapshot(
                month_index=index + 1,
                month=month_value,
                observed_at=observed_at,
                received_at=observed_at + timedelta(hours=8),
                repayment=repayment,
                operating=operating,
                models=models,
                review=review,
                source_ids=[
                    "bank_core",
                    "icbc_settlement",
                    *(["platform_meituan"] if platform_active_for_month else []),
                    "merchant_supplement",
                    "manual_verification",
                ],
                data_quality_status=data_quality,  # type: ignore[arg-type]
            )
            snapshots.append(snapshot)
            if review.alert_level != "LOW" or review.action in {"FREEZE", "MANUAL_REVIEW"}:
                alerts.append(
                    PostLoanAlert(
                        alert_id=f"PLA-{merchant_id}-{month_value:%Y%m}-{review.action}",
                        merchant_id=merchant_id,
                        occurred_at=observed_at,
                        level=review.alert_level,
                        alert_type=review.action,
                        title={
                            "DECREASE": "建议压降额度",
                            "FREEZE": "已冻结新增提款",
                            "MANUAL_REVIEW": "数据门控转人工复核",
                        }.get(review.action, "贷后风险预警"),
                        description="；".join(review.reasons),
                        evidence_refs=[review.review_id, *review.reason_codes],
                    )
                )

        final = snapshots[-1]
        final_outstanding = final.review.outstanding_principal
        available = 0 if frozen else max(0, current_limit - final_outstanding)
        account = LoanAccountSnapshot(
            loan_id=f"LN-{merchant_id}-202608",
            merchant_id=merchant_id,
            initial_limit=initial_limit,
            current_limit=current_limit,
            used_limit=final_outstanding,
            outstanding_principal=final_outstanding,
            available_limit=available,
            disbursed_at=date(2026, 8, 1),
            status="FROZEN" if frozen else "ACTIVE",
        )
        case = get_demo_case(merchant_id)
        return PostLoanTimeline(
            merchant_id=merchant_id,
            merchant_name=case.merchant.structural.merchant_name,
            scenario_name=scenario["name"],
            scenario_description=scenario["description"],
            as_of_month=final.month,
            current_month_index=visible_count,
            loan_account=account,
            source_statuses=source_statuses,
            snapshots=snapshots,
            alerts=alerts,
            submissions=state["submissions"],
            current_review=final.review,
            policy_notes=[
                "所有阈值均为竞赛模拟政策参数，不代表工商银行真实审批规则。",
                "风险事件持续监测，完整额度复评按月运行；LLM 不参与额度决策。",
                "提额需连续三个月良好表现，单次不超过 15%，批准后执行 90 天冷却期。",
                "降额不得低于未偿本金；严重风险冻结新增提款并转人工核查。",
            ],
        )


postloan_service = PostLoanService()
