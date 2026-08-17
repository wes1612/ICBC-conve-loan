"""Contracts for randomly selected simulated merchant demonstrations."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.anomaly import AnomalyAnalysisRequest
from app.schemas.cash_gap import CashGapForecastRequest
from app.schemas.full_analysis import OverallDecision
from app.schemas.material import MaterialEvidence
from app.schemas.merchant import MerchantAnalysisRequest


DemoMerchantId = Literal["M001", "M002", "M003", "M004", "M005"]


class DemoApplicant(BaseModel):
    merchant_name: str
    industry: str
    social_credit_code: str = Field(pattern=r"^[0-9A-Z]{18}$")
    province: str
    city: str
    address: str
    legal_name: str
    legal_phone: str
    legal_id_number: str
    contact_name: str
    contact_phone: str
    contact_id_number: str
    requested_amount: float = Field(gt=0)


class DemoCasePayload(BaseModel):
    merchant_id: DemoMerchantId
    case_label: str
    case_description: str
    expected_risk: Literal["LOW", "MEDIUM", "HIGH", "MANUAL_REVIEW"]
    expected_decision: OverallDecision
    applicant: DemoApplicant
    merchant: MerchantAnalysisRequest
    anomaly: AnomalyAnalysisRequest
    cash_gap: CashGapForecastRequest
    materials: list[MaterialEvidence]

