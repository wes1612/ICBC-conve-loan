"""商户分析请求模型。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

RuleProfile = Literal["v5_current", "legacy_acceptance"]
LegalCreditStatus = Literal["正常", "关注", "异常", "未知"]
ContractMatchStatus = Literal["通过", "失败", "待补充"]


class StructuralData(BaseModel):
    merchant_name: str
    industry: str
    license_subject: str
    account_holder: str | None = None
    invoice_issuer: str | None = None
    months_in_business: int = Field(ge=0)
    legal_credit_status: LegalCreditStatus
    employee_count: int = Field(ge=1)
    requested_amount: float = Field(gt=0)
    plan_score: float | None = Field(default=None, ge=0, le=100)
    missing_key_field_count: int = Field(default=0, ge=0, le=14)

    monthly_receipts: list[float]
    monthly_orders: list[float]
    monthly_redemption_rates: list[float | None]
    monthly_refund_rates: list[float | None]

    operating_cash_inflow_6m: float | None = Field(default=None, ge=0)
    operating_cash_outflow_6m: float | None = Field(default=None, ge=0)
    total_assets: float | None = Field(default=None, ge=0)
    total_liabilities: float | None = Field(default=None, ge=0)
    current_assets: float | None = Field(default=None, ge=0)
    current_liabilities: float | None = Field(default=None, ge=0)

    sales_invoice_amount_12m: float | None = Field(default=None, ge=0)
    purchase_invoice_amount_12m: float | None = Field(default=None, ge=0)
    invoice_count: int | None = Field(default=None, ge=0)
    valid_invoice_count: int | None = Field(default=None, ge=0)

    transaction_anomaly_hits: int = Field(default=0, ge=0)
    contract_invoice_match: ContractMatchStatus
    raw_inconsistency_count: int = Field(default=0, ge=0)
    peak_season_order_growth: float | None = None

    @model_validator(mode="after")
    def validate_series(self) -> "StructuralData":
        lengths = {
            len(self.monthly_receipts),
            len(self.monthly_orders),
            len(self.monthly_redemption_rates),
            len(self.monthly_refund_rates),
        }
        if len(lengths) != 1:
            raise ValueError("四组月度序列长度必须一致")
        if not lengths or next(iter(lengths)) < 6:
            raise ValueError("月度序列至少需要6期")
        return self


class UnstructuredData(BaseModel):
    valid_review_count: int = Field(ge=0)
    review_platform_count: int = Field(ge=0)
    average_rating: float | None = Field(default=None, ge=0, le=5)
    low_rating_ratio: float | None = Field(default=None, ge=0, le=1)
    sentiment_score: float | None = Field(default=None, ge=0, le=100)
    negative_review_ratio: float | None = Field(default=None, ge=0, le=1)
    keyword_risk_hits: int = Field(default=0, ge=0)
    merchant_reply_rate: float | None = Field(default=None, ge=0, le=1)
    review_interactions: int | None = Field(default=None, ge=0)
    media_review_ratio: float | None = Field(default=None, ge=0, le=1)
    suspected_ai_review_ratio: float | None = Field(default=None, ge=0, le=1)

    social_account_age_months: int | None = Field(default=None, ge=0)
    social_posts_per_month: float | None = Field(default=None, ge=0)
    follower_count: int | None = Field(default=None, ge=0)
    social_engagement_rate: float | None = Field(default=None, ge=0)
    social_negative_comment_ratio: float | None = Field(default=None, ge=0, le=1)
    ugc_count_90d: int | None = Field(default=None, ge=0)
    ugc_sentiment_score: float | None = Field(default=None, ge=0, le=100)

    complaint_source_count: int = Field(default=0, ge=0)
    complaint_count_6m: int = Field(default=0, ge=0)
    severe_complaint_ratio: float | None = Field(default=None, ge=0, le=1)
    complaint_completion_rate: float | None = Field(default=None, ge=0, le=1)
    complaint_amount_6m: float | None = Field(default=None, ge=0)


class MerchantAnalysisRequest(BaseModel):
    merchant_id: str
    profile: RuleProfile = "v5_current"
    structural: StructuralData
    unstructured: UnstructuredData

