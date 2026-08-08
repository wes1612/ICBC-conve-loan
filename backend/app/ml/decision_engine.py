"""额度、置信度和人工审核规则。"""

from __future__ import annotations

from app.ml.config import (
    KEYWORD_RISK_THRESHOLD,
    PROFILE_CONFIGS,
    REVIEW_ORDER_RATIO_THRESHOLD,
)
from app.schemas.analysis import (
    DimensionScores,
    FeatureSnapshot,
    LimitDecision,
    ReviewRuleHit,
)
from app.schemas.merchant import MerchantAnalysisRequest


def credit_grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 65:
        return "C"
    if score >= 50:
        return "D"
    return "E"


def score_multiplier(score: float) -> float | None:
    if score < 50:
        return None
    if score < 65:
        return 1.5
    if score < 80:
        return 2.5
    if score <= 90:
        return 3.5
    return 4.5


def growth_bonus(growth_score: float) -> float:
    if growth_score < 50:
        return 0.0
    if growth_score < 65:
        return 0.05
    if growth_score < 80:
        return 0.10
    if growth_score < 90:
        return 0.15
    return 0.20


def calculate_limit(
    request: MerchantAnalysisRequest,
    features: FeatureSnapshot,
    dimensions: DimensionScores,
    composite_score: float,
) -> LimitDecision:
    multiplier = score_multiplier(composite_score)
    stability_factor = dimensions.stability / 100
    capacity_factor = 0.9 + dimensions.capacity / 100 * 0.2
    bonus = growth_bonus(dimensions.growth)

    if multiplier is None:
        recommended = 0
    else:
        calculated = (
            round(features.average_receipt_6m)
            * multiplier
            * stability_factor
            * capacity_factor
            * (1 + bonus)
        )
        recommended = round(min(calculated, request.structural.requested_amount * 1.2))

    return LimitDecision(
        score_multiplier=multiplier,
        stability_factor=round(stability_factor, 4),
        capacity_factor=round(capacity_factor, 4),
        growth_bonus=bonus,
        recommended_limit=recommended,
    )


def confidence_level(
    request: MerchantAnalysisRequest,
    features: FeatureSnapshot,
) -> str:
    profile = PROFILE_CONFIGS[request.profile]
    ratio_abnormal = (
        features.review_order_ratio is not None
        and features.review_order_ratio > REVIEW_ORDER_RATIO_THRESHOLD
    )
    high = (
        features.data_completeness >= 0.90
        and features.final_inconsistency_count == 0
        and request.unstructured.valid_review_count > 0
        and not ratio_abnormal
    )
    if high:
        return "HIGH"

    if not profile["strict_confidence"]:
        return "MEDIUM"

    if (
        features.data_completeness >= 0.70
        and features.final_inconsistency_count <= 1
    ):
        return "MEDIUM"
    return "LOW"


def evaluate_review_rules(
    request: MerchantAnalysisRequest,
    features: FeatureSnapshot,
    confidence: str,
) -> list[ReviewRuleHit]:
    structural = request.structural
    unstructured = request.unstructured
    profile = PROFILE_CONFIGS[request.profile]
    hits: list[ReviewRuleHit] = []

    def add(code: str, level: str, message: str) -> None:
        hits.append(ReviewRuleHit(code=code, level=level, message=message))  # type: ignore[arg-type]

    if features.final_inconsistency_count >= 3:
        add("V01", "HIGH", "资料一致性异常数≥3")
    unresolved_ratio = None
    if unstructured.complaint_completion_rate is not None:
        unresolved_ratio = 1 - unstructured.complaint_completion_rate
    if unresolved_ratio is not None and unresolved_ratio > 0.50:
        add("V02", "HIGH", "未解决投诉占比>50%")
    if (
        unstructured.severe_complaint_ratio is not None
        and unstructured.severe_complaint_ratio > 0.30
    ):
        add("V03", "HIGH", "高严重度投诉占比>30%")
    if structural.transaction_anomaly_hits >= 1:
        add("V04", "HIGH", "流水异常模式命中")
    if structural.contract_invoice_match == "失败":
        add("V05", "HIGH", "合同发票匹配失败")
    if features.subject_consistency == "异常":
        add("V06", "HIGH", "三主体一致性异常")
    if structural.legal_credit_status == "异常":
        add("V07", "HIGH", "法人授信状态异常")
    if unstructured.keyword_risk_hits > KEYWORD_RISK_THRESHOLD:
        add("V08", "MEDIUM", "评价关键词风险命中数超过阈值")
    if (
        profile["enable_v09_review_rule"]
        and features.review_order_ratio is not None
        and features.review_order_ratio > REVIEW_ORDER_RATIO_THRESHOLD
    ):
        add("V09", "HIGH", "评价数/平台有效订单数比>50%")

    if confidence == "LOW":
        add("L01", "MEDIUM", "结果置信度低")
    if features.data_completeness < 0.60:
        add("L02", "MEDIUM", "数据完整性<60%")
    if (
        structural.months_in_business < 6
        and structural.requested_amount > features.average_receipt_6m * 3
    ):
        add("L04", "MEDIUM", "新商户申请额度超过月均收款3倍")

    return hits


def decision_and_risk(score: float, hits: list[ReviewRuleHit]) -> tuple[str, str]:
    if hits:
        return "MANUAL_REVIEW", "MANUAL_REVIEW"
    if score < 50:
        return "DECLINE", "HIGH"
    if score >= 80:
        return "APPROVE", "LOW"
    if score >= 65:
        return "APPROVE", "MEDIUM"
    return "APPROVE", "HIGH"


def explain_dimensions(dimensions: DimensionScores) -> tuple[list[str], list[str]]:
    labels = {
        "stability": "经营稳定性",
        "growth": "经营成长性",
        "authenticity": "经营真实性",
        "capacity": "消费承接能力",
        "online_reputation": "线上口碑",
        "social_activity": "社媒活跃度",
        "complaint_risk": "投诉风险控制",
    }
    values = dimensions.model_dump(exclude={"unstructured"})
    ranked = sorted(values.items(), key=lambda item: item[1], reverse=True)
    positive = [f"{labels[name]}表现良好（{value:.1f}分）" for name, value in ranked if value >= 80][:3]
    negative = [
        f"{labels[name]}需要关注（{value:.1f}分）"
        for name, value in reversed(ranked)
        if value < 60
    ][:3]
    return positive, negative
