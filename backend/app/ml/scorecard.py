"""v5 与历史验收口径的可解释评分卡。"""

from __future__ import annotations

from collections.abc import Mapping

from app.ml.config import (
    AUTHENTICITY_WEIGHTS,
    CAPACITY_WEIGHTS,
    COMPLAINT_WEIGHTS,
    COMPOSITE_WEIGHTS,
    GROWTH_WEIGHTS,
    NEUTRAL_SCORE,
    PROFILE_CONFIGS,
    SOCIAL_WEIGHTS,
    STABILITY_WEIGHTS,
)
from app.schemas.analysis import DimensionScores, FeatureSnapshot
from app.schemas.merchant import MerchantAnalysisRequest


def _weighted(scores: Mapping[str, float], weights: Mapping[str, float]) -> float:
    return sum(scores[name] * weight for name, weight in weights.items())


def _tenure_score(months: int) -> float:
    if months < 6:
        return 0
    if months < 12:
        return 40
    if months < 36:
        return 70
    return 100


def _active_month_score(months: int) -> float:
    if months <= 2:
        return 0
    if months <= 4:
        return 50
    return 100


def _volatility_score(value: float | None) -> float:
    if value is None:
        return NEUTRAL_SCORE
    if value > 0.50:
        return 0
    if value >= 0.30:
        return 40
    if value >= 0.15:
        return 70
    return 100


def _max_month_share_score(value: float | None) -> float:
    if value is None:
        return NEUTRAL_SCORE
    if value > 0.60:
        return 0
    if value >= 0.40:
        return 50
    return 100


def _cashflow_margin_score(value: float | None) -> float:
    if value is None:
        return NEUTRAL_SCORE
    if value < 0:
        return 0
    if value < 0.10:
        return 40
    if value <= 0.25:
        return 70
    return 100


def _debt_ratio_score(value: float | None) -> float:
    if value is None:
        return NEUTRAL_SCORE
    if value > 0.70:
        return 0
    if value >= 0.50:
        return 50
    return 100


def _current_ratio_score(value: float | None) -> float:
    if value is None:
        return NEUTRAL_SCORE
    if value < 1:
        return 0
    if value <= 1.5:
        return 60
    return 100


def _refund_rate_score(value: float | None) -> float:
    if value is None:
        return NEUTRAL_SCORE
    if value > 0.15:
        return 0
    if value >= 0.08:
        return 50
    return 100


def _growth_score(value: float | None) -> float:
    if value is None:
        return NEUTRAL_SCORE
    if value < 0:
        return 0
    if value <= 0.05:
        return 40
    if value <= 0.15:
        return 70
    return 100


def _inverse_diff_score(value: float | None) -> float:
    if value is None:
        return NEUTRAL_SCORE
    if value > 0.30:
        return 0
    if value > 0.15:
        return 40
    if value > 0.05:
        return 70
    return 100


def _correlation_score(value: float | None) -> float:
    if value is None:
        return NEUTRAL_SCORE
    if value < 0.30:
        return 0
    if value <= 0.60:
        return 50
    return 100


def _invoice_ratio_score(value: float | None) -> float:
    if value is None:
        return NEUTRAL_SCORE
    if value < 0.70:
        return 0
    if value <= 0.90:
        return 60
    return 100


def _inconsistency_score(value: int) -> float:
    if value >= 3:
        return 0
    if value >= 1:
        return 50
    return 100


def _monthly_orders_score(value: float) -> float:
    if value < 50:
        return 0
    if value <= 200:
        return 40
    if value <= 500:
        return 70
    return 100


def _redemption_score(value: float | None) -> float:
    if value is None:
        return NEUTRAL_SCORE
    if value < 0.70:
        return 0
    if value < 0.85:
        return 50
    if value <= 0.95:
        return 80
    return 100


def _employee_score(value: int) -> float:
    if value <= 2:
        return 30
    if value <= 5:
        return 60
    if value <= 10:
        return 80
    return 100


def _utilization_score(value: float | None) -> float:
    if value is None:
        return NEUTRAL_SCORE
    if value < 0.50:
        return 0
    if value < 0.70:
        return 50
    if value <= 0.90:
        return 80
    return 100


def _peak_growth_score(value: float | None) -> float:
    if value is None:
        return NEUTRAL_SCORE
    if value < 0:
        return 0
    if value <= 0.10:
        return 40
    if value <= 0.30:
        return 70
    return 100


def _rating_score(value: float | None) -> float:
    if value is None:
        return NEUTRAL_SCORE
    if value < 3.5:
        return 0
    if value <= 4.0:
        return 40
    if value <= 4.5:
        return 70
    return 100


def _negative_ratio_score(value: float | None) -> float:
    if value is None:
        return NEUTRAL_SCORE
    if value > 0.20:
        return 0
    if value > 0.10:
        return 40
    if value >= 0.05:
        return 70
    return 100


def _media_ratio_score(value: float | None) -> float:
    if value is None:
        return NEUTRAL_SCORE
    if value < 0.10:
        return 0
    if value <= 0.30:
        return 50
    return 100


def _ai_ratio_score(value: float | None) -> float:
    if value is None:
        return NEUTRAL_SCORE
    if value > 0.30:
        return 0
    if value > 0.15:
        return 40
    if value >= 0.05:
        return 70
    return 100


def _social_age_score(value: int | None) -> float:
    if value is None:
        return NEUTRAL_SCORE
    if value < 6:
        return 0
    if value < 12:
        return 40
    if value <= 36:
        return 70
    return 100


def _posting_score(value: float | None) -> float:
    if value is None:
        return NEUTRAL_SCORE
    if value < 1:
        return 0
    if value < 4:
        return 40
    if value <= 12:
        return 70
    return 100


def _engagement_score(value: float | None) -> float:
    if value is None:
        return NEUTRAL_SCORE
    if value < 0.01:
        return 0
    if value < 0.03:
        return 40
    if value < 0.05:
        return 70
    return 100


def _ugc_score(value: int | None) -> float:
    if value is None:
        return NEUTRAL_SCORE
    if value < 5:
        return 0
    if value < 20:
        return 40
    if value <= 50:
        return 70
    return 100


def _severe_complaint_score(value: float | None) -> float:
    if value is None:
        return NEUTRAL_SCORE
    if value > 0.30:
        return 0
    if value > 0.15:
        return 40
    if value > 0.05:
        return 70
    return 100


def _completion_score(value: float | None) -> float:
    if value is None:
        return NEUTRAL_SCORE
    if value < 0.50:
        return 0
    if value < 0.70:
        return 40
    if value <= 0.90:
        return 70
    return 100


def _complaint_amount_score(value: float | None) -> float:
    if value is None:
        return NEUTRAL_SCORE
    if value > 0.05:
        return 0
    if value > 0.02:
        return 40
    if value > 0.01:
        return 70
    return 100


def _complaint_count_score(value: float) -> float:
    if value > 20:
        return 0
    if value > 10:
        return 40
    if value >= 5:
        return 70
    return 100


def legal_credit_score(status: str) -> float:
    return {"正常": 100, "关注": 50, "异常": 0, "未知": 40}[status]


def calculate_dimensions(
    request: MerchantAnalysisRequest,
    features: FeatureSnapshot,
) -> DimensionScores:
    structural = request.structural
    unstructured = request.unstructured
    profile = PROFILE_CONFIGS[request.profile]

    stability = _weighted(
        {
            "tenure": _tenure_score(structural.months_in_business),
            "active_months": _active_month_score(features.active_months_6m),
            "receipt_volatility": _volatility_score(features.receipt_volatility),
            "max_month_share": _max_month_share_score(features.max_month_receipt_share),
            "operating_cashflow_margin": _cashflow_margin_score(features.operating_cashflow_margin_6m),
            "debt_ratio": _debt_ratio_score(features.debt_ratio),
            "current_ratio": _current_ratio_score(features.current_ratio),
            "refund_rate": _refund_rate_score(features.refund_rate_6m),
        },
        STABILITY_WEIGHTS,
    )

    growth = _weighted(
        {
            "mom_receipt_growth": _growth_score(features.receipt_mom_growth),
            "receipt_cagr_6m": _growth_score(features.receipt_cagr_6m),
            "order_growth_6m": _growth_score(features.platform_order_growth_6m),
            "plan_score": structural.plan_score if structural.plan_score is not None else NEUTRAL_SCORE,
        },
        GROWTH_WEIGHTS,
    )

    inconsistency = (
        features.final_inconsistency_count
        if profile["authenticity_uses_final_inconsistency"]
        else features.structured_inconsistency_count
    )
    authenticity = _weighted(
        {
            "invoice_receipt_diff": _inverse_diff_score(features.invoice_receipt_diff),
            "cashflow_receipt_diff": _inverse_diff_score(features.cashflow_receipt_diff),
            "order_receipt_correlation": _correlation_score(features.order_receipt_correlation),
            "valid_invoice_ratio": _invoice_ratio_score(features.valid_invoice_ratio),
            "inconsistency_count": _inconsistency_score(inconsistency),
        },
        AUTHENTICITY_WEIGHTS,
    )

    capacity = _weighted(
        {
            "monthly_orders": _monthly_orders_score(features.monthly_orders_6m),
            "redemption_rate": _redemption_score(features.redemption_rate_6m),
            "employee_count": _employee_score(structural.employee_count),
            "utilization": _utilization_score(features.capacity_utilization),
            "peak_season_growth": _peak_growth_score(features.peak_season_order_growth),
        },
        CAPACITY_WEIGHTS,
    )

    online_scores = {
        "average_rating": _rating_score(unstructured.average_rating),
        "sentiment": unstructured.sentiment_score if unstructured.sentiment_score is not None else NEUTRAL_SCORE,
        "negative_ratio": _negative_ratio_score(unstructured.negative_review_ratio),
        "media_ratio": _media_ratio_score(unstructured.media_review_ratio),
        "ai_ratio": _ai_ratio_score(unstructured.suspected_ai_review_ratio),
    }
    online = _weighted(
        online_scores,
        profile["online_reputation_weights"],  # type: ignore[arg-type]
    )

    social = _weighted(
        {
            "account_age": _social_age_score(unstructured.social_account_age_months),
            "posting_frequency": _posting_score(unstructured.social_posts_per_month),
            "engagement_rate": _engagement_score(unstructured.social_engagement_rate),
            "ugc_count": _ugc_score(unstructured.ugc_count_90d),
        },
        SOCIAL_WEIGHTS,
    )

    complaint_amount_ratio = None
    if unstructured.complaint_amount_6m is not None and features.receipts_12m > 0:
        complaint_amount_ratio = unstructured.complaint_amount_6m / features.receipts_12m
    complaint = _weighted(
        {
            "severe_ratio": _severe_complaint_score(unstructured.severe_complaint_ratio),
            "completion_rate": _completion_score(unstructured.complaint_completion_rate),
            "amount_ratio": _complaint_amount_score(complaint_amount_ratio),
            "monthly_count": _complaint_count_score(unstructured.complaint_count_6m / 6),
        },
        COMPLAINT_WEIGHTS,
    )

    unstructured_score = online * 0.50 + social * 0.20 + complaint * 0.30

    return DimensionScores(
        stability=round(stability, 1),
        growth=round(growth, 1),
        authenticity=round(authenticity, 1),
        capacity=round(capacity, 1),
        online_reputation=round(online, 1),
        social_activity=round(social, 1),
        complaint_risk=round(complaint, 1),
        unstructured=round(unstructured_score, 1),
    )


def calculate_composite(
    request: MerchantAnalysisRequest,
    features: FeatureSnapshot,
    dimensions: DimensionScores,
) -> float:
    score = _weighted(
        {
            "stability": dimensions.stability,
            "growth": dimensions.growth,
            "authenticity": dimensions.authenticity,
            "unstructured": dimensions.unstructured,
            "completeness": features.data_completeness * 100,
            "legal_credit": legal_credit_score(request.structural.legal_credit_status),
        },
        COMPOSITE_WEIGHTS,
    )
    return round(score, 1)
