"""一次性聚合分析的前后端稳定契约。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, model_validator

from app.schemas.analysis import AnalysisResult
from app.schemas.anomaly import AnomalyAnalysisRequest, AnomalyAnalysisResult
from app.schemas.cash_gap import CashGapForecastRequest, CashGapForecastResult
from app.schemas.merchant import MerchantAnalysisRequest


ModuleState = Literal["READY", "NOT_PROVIDED"]


class FullAnalysisRequest(BaseModel):
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
        return self


class ModuleStates(BaseModel):
    score: Literal["READY"] = "READY"
    anomaly: ModuleState
    cash_gap: ModuleState


class FullAnalysisResult(BaseModel):
    merchant_id: str
    generated_at: datetime
    overall_risk: Literal["LOW", "MEDIUM", "HIGH", "MANUAL_REVIEW"]
    module_states: ModuleStates
    data_warnings: list[str]
    score: AnalysisResult
    anomaly: AnomalyAnalysisResult | None
    cash_gap: CashGapForecastResult | None
    api_version: str = "0.2.0"

