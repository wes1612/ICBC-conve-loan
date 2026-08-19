"""一次性聚合分析的前后端稳定契约。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.analysis import AnalysisResult
from app.schemas.anomaly import AnomalyAnalysisRequest, AnomalyAnalysisResult
from app.schemas.cash_gap import CashGapForecastRequest, CashGapForecastResult
from app.schemas.merchant import MerchantAnalysisRequest
from app.schemas.material import MaterialEvidence


ModuleState = Literal["READY", "NOT_PROVIDED"]
OverallDecision = Literal["APPROVE", "MANUAL_REVIEW", "DECLINE"]
DataGroup = Literal["cashflow", "statement", "tax", "plan"]
UseOfFunds = Literal["设备采购", "装修扩店", "旺季备货", "人员扩充", "平台活动垫资", "租金工资周转", "其他经营周转"]
RepaymentSource = Literal["经营现金流", "平台订单回款", "工行账户自动扣款", "其他经营收入"]
AuthorizedSource = Literal[
    "bank",
    "unionpay",
    "alipay",
    "wechat",
    "meituan",
    "douyin",
    "xiaohongshu",
    "enterprise",
]


class ApplicationContext(BaseModel):
    """申请流程和授权证据；只用于校验与审计，不直接参与评分。"""

    social_credit_code: str = Field(pattern=r"^[0-9A-Z]{18}$")
    province: str | None = Field(default=None, min_length=2, max_length=30)
    city: str | None = Field(default=None, min_length=2, max_length=30)
    operating_address: str = Field(min_length=5, max_length=200)
    legal_name: str = Field(min_length=2, max_length=50)
    legal_phone: str | None = Field(default=None, pattern=r"^1[3-9]\d{9}$")
    legal_id_number: str | None = Field(default=None, pattern=r"^\d{17}[0-9X]$")
    contact_name: str | None = Field(default=None, min_length=2, max_length=50)
    contact_phone: str = Field(pattern=r"^1[3-9]\d{9}$")
    contact_id_number: str | None = Field(default=None, pattern=r"^\d{17}[0-9X]$")
    industry: str = Field(default="生活服务", min_length=2, max_length=30)
    requested_amount: int = Field(default=100_000, gt=0, le=20_000_000)
    use_of_funds: UseOfFunds = "其他经营周转"
    requested_tenor_months: int = Field(default=12, ge=3, le=24)
    expected_repayment_source: RepaymentSource = "经营现金流"
    identity_verified: bool
    uploaded_data_groups: list[DataGroup]
    authorized_sources: list[AuthorizedSource]
    consent_confirmed: bool
    consent_version: str = Field(default="consent_v1_2026_08", min_length=3, max_length=40)
    consented_at: datetime | None = None
    materials: list[MaterialEvidence]

    @model_validator(mode="after")
    def validate_application_state(self) -> "ApplicationContext":
        if not self.identity_verified:
            raise ValueError("法人身份尚未完成核验")
        if not self.consent_confirmed or self.consented_at is None:
            raise ValueError("数据授权尚未明确确认")
        if len(self.uploaded_data_groups) != len(set(self.uploaded_data_groups)):
            raise ValueError("uploaded_data_groups 不能重复")
        if len(self.authorized_sources) != len(set(self.authorized_sources)):
            raise ValueError("authorized_sources 不能重复")
        material_ids = [material.material_id for material in self.materials]
        if len(material_ids) != len(set(material_ids)):
            raise ValueError("materials 中的 material_id 不能重复")
        return self


class FullAnalysisRequest(BaseModel):
    application: ApplicationContext
    merchant: MerchantAnalysisRequest
    anomaly: AnomalyAnalysisRequest | None = None
    cash_gap: CashGapForecastRequest | None = None

    @model_validator(mode="after")
    def validate_merchant_ids(self) -> "FullAnalysisRequest":
        merchant_id = self.merchant.merchant_id
        if self.anomaly and self.anomaly.merchant_id != merchant_id:
            raise ValueError("anomaly.merchant_id 必须与 merchant.merchant_id 一致")
        if self.cash_gap and self.cash_gap.merchant_id != merchant_id:
            raise ValueError("cash_gap.merchant_id 必须与 merchant.merchant_id 一致")

        groups = set(self.application.uploaded_data_groups)
        sources = set(self.application.authorized_sources)
        material_groups = {
            material.group
            for material in self.application.materials
            if material.parse_status == "PARSED"
        }
        if any(
            material.merchant_id != merchant_id
            for material in self.application.materials
        ):
            raise ValueError("所有材料的 merchant_id 必须与申请商户一致")
        if "license" not in material_groups:
            raise ValueError("缺少已解析的经营主体证明")
        required_score_groups = {"cashflow", "statement", "tax"}
        required_score_sources = {"bank", "meituan", "enterprise"}
        if missing := required_score_groups - groups:
            raise ValueError(f"评分缺少资料组：{', '.join(sorted(missing))}")
        required_material_groups = required_score_groups | {"plan"}
        if missing := required_material_groups - material_groups:
            raise ValueError(f"缺少已解析材料：{', '.join(sorted(missing))}")
        if groups != material_groups.intersection({"cashflow", "statement", "tax", "plan"}):
            raise ValueError("uploaded_data_groups 必须与已解析材料组一致")
        if missing := required_score_sources - sources:
            raise ValueError(f"评分缺少授权来源：{', '.join(sorted(missing))}")
        if self.anomaly and not sources.intersection(
            {"bank", "unionpay", "alipay", "wechat"}
        ):
            raise ValueError("异常识别缺少交易数据授权")
        if self.cash_gap and ({"cashflow", "plan"} - groups or "bank" not in sources):
            raise ValueError("资金缺口预测需要现金流、经营计划和银行流水授权")
        return self


class ModuleStates(BaseModel):
    score: Literal["READY"] = "READY"
    anomaly: ModuleState
    cash_gap: ModuleState


class EligibilityResult(BaseModel):
    status: Literal["ELIGIBLE", "SUPPLEMENT_REQUIRED", "OUT_OF_SCOPE", "MANUAL_REVIEW"]
    conclusion: str
    pilot_industry: bool
    reasons: list[str]
    warnings: list[str]


class LoanTerms(BaseModel):
    requested_amount: int
    recommended_limit: int
    limit_range: list[int] = Field(min_length=2, max_length=2)
    tenor_months: int
    repayment_method: str
    is_revolving: bool
    drawdown_rule: str
    renewal_rule: str
    limit_adjustment_rule: str
    use_of_funds: UseOfFunds
    use_of_funds_match: str
    use_of_funds_warnings: list[str]
    expected_repayment_source: RepaymentSource
    repayment_source_note: str


class RepaymentCapacity(BaseModel):
    conclusion: str
    confidence: Literal["LOW", "MEDIUM", "HIGH"]
    monthly_operating_inflow: float | None
    monthly_operating_outflow: float | None
    fixed_cost_coverage: float | None
    p90_funding_gap: float | None
    debt_pressure_level: str
    refund_complaint_pressure: str
    evidence: list[str]


class AuditTrail(BaseModel):
    consent_version: str
    consent_timestamp: datetime | None
    authorized_sources: list[AuthorizedSource]
    material_hashes: dict[str, str]
    material_ids: list[str]
    score_version: str
    rules_version: str
    model_version: str
    generated_at: datetime
    ai_used: bool




class PolicyRecommendation(BaseModel):
    policy_id: str
    policy_name: str
    policy_type: str
    policy_level: str
    support_method: str
    support_standard: str
    match_level: Literal["HIGH", "MEDIUM", "LOW", "CANDIDATE"]
    reason: str
    required_materials: list[str]
    application_steps: list[str]
    bank_actions: list[str]
    consumer_introduction: list[str]
    source_url: str | None
    application_deadline: str | None
    status: Literal["ACTIVE", "DRAFT", "EXPIRED"]
    warnings: list[str]

class FullAnalysisResult(BaseModel):
    merchant_id: str
    generated_at: datetime
    overall_risk: Literal["LOW", "MEDIUM", "HIGH", "MANUAL_REVIEW"]
    overall_decision: OverallDecision
    module_states: ModuleStates
    data_warnings: list[str]
    score: AnalysisResult
    anomaly: AnomalyAnalysisResult | None
    cash_gap: CashGapForecastResult | None
    material_evidence: list[MaterialEvidence]
    eligibility: EligibilityResult
    loan_terms: LoanTerms
    repayment_capacity: RepaymentCapacity
    audit_trail: AuditTrail
    policy_recommendations: list[PolicyRecommendation] = Field(default_factory=list)
    api_version: str = "0.4.0"

