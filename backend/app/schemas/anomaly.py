"""交易异常识别的输入与输出契约。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class TransactionDetail(BaseModel):
    merchant_id: str
    transaction_id: str
    transaction_time: datetime
    direction: Literal["IN", "OUT"]
    amount: float = Field(gt=0)
    counterparty_hash: str
    channel: Literal["COLLECTION", "TRANSFER", "CASH", "REFUND", "REVERSAL"]
    status: Literal["SUCCESS", "REFUNDED", "REVERSED"] = "SUCCESS"
    order_id_hash: str | None = None
    invoice_id_hash: str | None = None
    purpose_code: str | None = None
    is_business_hour: bool


class AnomalyAnalysisRequest(BaseModel):
    merchant_id: str
    as_of_time: datetime | None = None
    transactions: list[TransactionDetail] = Field(min_length=5)

    @model_validator(mode="after")
    def validate_transactions(self) -> "AnomalyAnalysisRequest":
        if any(item.merchant_id != self.merchant_id for item in self.transactions):
            raise ValueError("交易明细中的 merchant_id 必须与请求一致")
        ids = [item.transaction_id for item in self.transactions]
        if len(ids) != len(set(ids)):
            raise ValueError("transaction_id 不得重复")
        if self.as_of_time and any(
            item.transaction_time > self.as_of_time for item in self.transactions
        ):
            raise ValueError("交易时间不得晚于 as_of_time")
        return self


class AnomalyRuleHit(BaseModel):
    code: str
    level: Literal["HIGH", "MEDIUM"]
    contribution: int = Field(ge=0, le=100)
    message: str
    evidence_transaction_ids: list[str]


class AnomalyAnalysisResult(BaseModel):
    merchant_id: str
    evaluated_at: datetime
    transaction_count: int
    recent_transaction_count: int
    anomaly_score: int = Field(ge=0, le=100)
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    confidence: Literal["LOW", "MEDIUM", "HIGH"]
    reason_codes: list[str]
    rule_hits: list[AnomalyRuleHit]
    evidence_transaction_ids: list[str]
    model_version: str = "anomaly_hybrid_v1"

