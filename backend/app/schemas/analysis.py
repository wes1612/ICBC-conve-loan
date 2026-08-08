"""分析结果模型。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class FeatureSnapshot(BaseModel):
    receipts_6m: float
    receipts_12m: float
    average_receipt_6m: float
    receipt_mom_growth: float | None
    receipt_cagr_6m: float | None
    receipt_volatility: float | None
    max_month_receipt_share: float | None
    active_months_6m: int
    operating_cashflow_margin_6m: float | None
    debt_ratio: float | None
    current_ratio: float | None
    platform_orders_6m: float
    platform_order_growth_6m: float | None
    redemption_rate_6m: float | None
    refund_rate_6m: float | None
    effective_orders_6m: float | None
    estimated_ticket_6m: float | None
    invoice_receipt_diff: float | None
    cashflow_receipt_diff: float | None
    order_receipt_correlation: float | None
    valid_invoice_ratio: float | None
    subject_consistency: Literal["通过", "异常", "待补充"]
    data_completeness: float
    structured_inconsistency_count: int
    final_inconsistency_count: int
    review_order_ratio: float | None
    monthly_orders_6m: float
    capacity_utilization: float | None
    peak_season_order_growth: float | None


class DimensionScores(BaseModel):
    stability: float
    growth: float
    authenticity: float
    capacity: float
    online_reputation: float
    social_activity: float
    complaint_risk: float
    unstructured: float


class LimitDecision(BaseModel):
    score_multiplier: float | None
    stability_factor: float
    capacity_factor: float
    growth_bonus: float
    recommended_limit: int


class ReviewRuleHit(BaseModel):
    code: str
    level: Literal["HIGH", "MEDIUM"]
    message: str


class AnalysisResult(BaseModel):
    merchant_id: str
    merchant_name: str
    profile: str
    score_version: str
    features: FeatureSnapshot
    dimensions: DimensionScores
    operating_credit_score: float
    credit_grade: Literal["A", "B", "C", "D", "E"]
    risk_band: Literal["LOW", "MEDIUM", "HIGH", "MANUAL_REVIEW"]
    pd_12m: None = None
    pd_status: Literal["UNCALIBRATED"] = "UNCALIBRATED"
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    decision: Literal["APPROVE", "MANUAL_REVIEW", "DECLINE"]
    review_required: bool
    review_rules: list[ReviewRuleHit]
    positive_reasons: list[str]
    negative_reasons: list[str]
    limit: LimitDecision

