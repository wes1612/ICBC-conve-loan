"""评分卡的版本化业务配置。

阈值来自 v5 数据字典。两个 profile 的差异是数据字典 v5 与现有
五商户验收表之间已经确认的口径差异，不是两套随意的算法。
"""

from __future__ import annotations

from typing import Final

NEUTRAL_SCORE: Final[float] = 60.0
COMPLETENESS_FIELD_COUNT: Final[int] = 14
REVIEW_ORDER_RATIO_THRESHOLD: Final[float] = 0.50
KEYWORD_RISK_THRESHOLD: Final[int] = 3

INDUSTRY_MONTHLY_CAPACITY_PER_EMPLOYEE: Final[dict[str, float]] = {
    "美容美发": 65.0,
    "宠物服务": 78.0,
}

STABILITY_WEIGHTS: Final[dict[str, float]] = {
    "tenure": 0.15,
    "active_months": 0.10,
    "receipt_volatility": 0.20,
    "max_month_share": 0.10,
    "operating_cashflow_margin": 0.20,
    "debt_ratio": 0.10,
    "current_ratio": 0.05,
    "refund_rate": 0.10,
}

GROWTH_WEIGHTS: Final[dict[str, float]] = {
    "mom_receipt_growth": 0.25,
    "receipt_cagr_6m": 0.35,
    "order_growth_6m": 0.25,
    "plan_score": 0.15,
}

AUTHENTICITY_WEIGHTS: Final[dict[str, float]] = {
    "invoice_receipt_diff": 0.25,
    "cashflow_receipt_diff": 0.20,
    "order_receipt_correlation": 0.20,
    "valid_invoice_ratio": 0.15,
    "inconsistency_count": 0.20,
}

CAPACITY_WEIGHTS: Final[dict[str, float]] = {
    "monthly_orders": 0.25,
    "redemption_rate": 0.25,
    "employee_count": 0.20,
    "utilization": 0.15,
    "peak_season_growth": 0.15,
}

SOCIAL_WEIGHTS: Final[dict[str, float]] = {
    "account_age": 0.20,
    "posting_frequency": 0.25,
    "engagement_rate": 0.30,
    "ugc_count": 0.25,
}

COMPLAINT_WEIGHTS: Final[dict[str, float]] = {
    "severe_ratio": 0.30,
    "completion_rate": 0.30,
    "amount_ratio": 0.20,
    "monthly_count": 0.20,
}

COMPOSITE_WEIGHTS: Final[dict[str, float]] = {
    "stability": 0.30,
    "growth": 0.20,
    "authenticity": 0.20,
    "unstructured": 0.15,
    "completeness": 0.10,
    "legal_credit": 0.05,
}

PROFILE_CONFIGS: Final[dict[str, dict[str, object]]] = {
    "legacy_acceptance": {
        "score_version": "scorecard_legacy_acceptance_2026_07",
        "online_reputation_weights": {
            "average_rating": 0.40,
            "sentiment": 0.20,
            "negative_ratio": 0.20,
            "media_ratio": 0.10,
            "ai_ratio": 0.10,
        },
        "authenticity_uses_final_inconsistency": False,
        "strict_confidence": False,
        "enable_v09_review_rule": False,
    },
    "v5_current": {
        "score_version": "scorecard_v5_2026_08",
        "online_reputation_weights": {
            "average_rating": 0.30,
            "sentiment": 0.10,
            "negative_ratio": 0.20,
            "media_ratio": 0.20,
            "ai_ratio": 0.20,
        },
        "authenticity_uses_final_inconsistency": True,
        "strict_confidence": True,
        "enable_v09_review_rule": True,
    },
}

