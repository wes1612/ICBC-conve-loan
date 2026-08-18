"""贷后动态监测与额度复评的稳定 API 契约。"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


PostLoanAction = Literal[
    "INCREASE",
    "MAINTAIN",
    "DECREASE",
    "FREEZE",
    "MANUAL_REVIEW",
]
AlertLevel = Literal["LOW", "MEDIUM", "HIGH"]
AuthorizationStatus = Literal["ACTIVE", "EXPIRED", "REVOKED", "NOT_REQUIRED"]
DataQualityStatus = Literal["VERIFIED", "REPORTED", "MISSING", "CONFLICT"]
ReviewStatus = Literal["AUTO_APPLIED", "PENDING_REVIEW", "APPROVED", "REJECTED"]
LoanStatus = Literal["ACTIVE", "FROZEN", "CLOSED"]
SourceType = Literal[
    "BANK_INTERNAL_SIMULATED",
    "PLATFORM_AUTHORIZED_SIMULATED",
    "MERCHANT_SUBMITTED_SIMULATED",
    "MANUAL_VERIFIED_SIMULATED",
]


class PostLoanSourceStatus(BaseModel):
    source_id: str
    display_name: str
    source_type: SourceType
    authorization_status: AuthorizationStatus
    scopes: list[str]
    last_synced_at: datetime | None = None
    expires_at: date | None = None
    freshness_hours: int | None = Field(default=None, ge=0)
    quality_status: DataQualityStatus
    verified: bool
    record_count: int = Field(default=0, ge=0)


class LoanAccountSnapshot(BaseModel):
    loan_id: str
    merchant_id: str
    initial_limit: float = Field(ge=0)
    current_limit: float = Field(ge=0)
    used_limit: float = Field(ge=0)
    outstanding_principal: float = Field(ge=0)
    available_limit: float = Field(ge=0)
    disbursed_at: date
    status: LoanStatus


class RepaymentPerformance(BaseModel):
    due_date: date
    scheduled_amount: float = Field(ge=0)
    paid_amount: float = Field(ge=0)
    payment_date: date | None = None
    days_past_due: int = Field(ge=0)
    on_time: bool


class MonthlyOperatingMetrics(BaseModel):
    receipts: float = Field(ge=0)
    receipt_mom_growth: float | None = None
    orders: int = Field(ge=0)
    refund_rate: float = Field(ge=0, le=1)
    complaint_count: int = Field(ge=0)
    cash_balance: float = Field(ge=0)
    limit_utilization: float = Field(ge=0, le=1)
    compliant_use_ratio: float = Field(ge=0, le=1)


class PostLoanModelSnapshot(BaseModel):
    operating_credit_score: float = Field(ge=0, le=100)
    credit_grade: Literal["A", "B", "C", "D", "E"]
    anomaly_score: int = Field(ge=0, le=100)
    anomaly_risk: Literal["LOW", "MEDIUM", "HIGH"]
    max_p90_funding_gap: float = Field(ge=0)
    cash_gap_risk: Literal["LOW", "MEDIUM", "HIGH"]
    confidence: Literal["LOW", "MEDIUM", "HIGH"]
    score_model_version: str
    anomaly_model_version: str
    cash_gap_model_version: str


class CreditReviewResult(BaseModel):
    review_id: str
    review_month: date
    action: PostLoanAction
    current_limit: float = Field(ge=0)
    candidate_limit: float = Field(ge=0)
    proposed_limit: float = Field(ge=0)
    outstanding_principal: float = Field(ge=0)
    alert_level: AlertLevel
    reason_codes: list[str]
    reasons: list[str]
    status: ReviewStatus
    next_review_date: date
    policy_version: str = "postloan_competition_policy_v1"
    reviewer_note: str | None = None


class PostLoanMonthlySnapshot(BaseModel):
    month_index: int = Field(ge=1, le=12)
    month: date
    observed_at: datetime
    received_at: datetime
    repayment: RepaymentPerformance
    operating: MonthlyOperatingMetrics
    models: PostLoanModelSnapshot
    review: CreditReviewResult
    source_ids: list[str]
    data_quality_status: DataQualityStatus


class PostLoanAlert(BaseModel):
    alert_id: str
    merchant_id: str
    occurred_at: datetime
    level: AlertLevel
    alert_type: str
    title: str
    description: str
    status: Literal["OPEN", "ACKNOWLEDGED", "CLOSED"] = "OPEN"
    evidence_refs: list[str] = Field(default_factory=list)


class MerchantSubmission(BaseModel):
    submission_id: str
    merchant_id: str
    category: Literal["OFF_BANK_STATEMENT", "CONTRACT", "PURPOSE_PROOF", "EXPLANATION"]
    description: str
    file_name: str | None = None
    submitted_at: datetime
    source_type: Literal["MERCHANT_SUBMITTED_SIMULATED"] = "MERCHANT_SUBMITTED_SIMULATED"
    verification_status: Literal["PENDING", "VERIFIED", "REJECTED"] = "PENDING"


class MerchantSubmissionRequest(BaseModel):
    category: Literal["OFF_BANK_STATEMENT", "CONTRACT", "PURPOSE_PROOF", "EXPLANATION"]
    description: str = Field(min_length=5, max_length=500)
    file_name: str | None = Field(default=None, max_length=150)


class SourceAuthorizationRequest(BaseModel):
    action: Literal["RENEW", "REVOKE"]
    expires_at: date | None = None

    @model_validator(mode="after")
    def validate_renewal(self) -> "SourceAuthorizationRequest":
        if self.action == "RENEW" and self.expires_at is None:
            raise ValueError("续期授权必须提供 expires_at")
        return self


class ReviewDecisionRequest(BaseModel):
    decision: Literal["APPROVE", "MAINTAIN", "ESCALATE"]
    approved_limit: float | None = Field(default=None, gt=0)
    note: str | None = Field(default=None, max_length=300)


class PostLoanTimeline(BaseModel):
    merchant_id: str
    merchant_name: str
    scenario_name: str
    scenario_description: str
    simulated: Literal[True] = True
    as_of_month: date
    current_month_index: int = Field(ge=1, le=12)
    total_months: Literal[12] = 12
    loan_account: LoanAccountSnapshot
    source_statuses: list[PostLoanSourceStatus]
    snapshots: list[PostLoanMonthlySnapshot]
    alerts: list[PostLoanAlert]
    submissions: list[MerchantSubmission]
    current_review: CreditReviewResult
    policy_notes: list[str]

