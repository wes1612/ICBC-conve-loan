"""资金缺口预测的输入与输出契约。"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class MonthlyCashflow(BaseModel):
    month: date
    operating_inflow: float = Field(ge=0)
    operating_outflow: float = Field(ge=0)


class CashGapForecastRequest(BaseModel):
    merchant_id: str
    snapshot_date: date
    history: list[MonthlyCashflow] = Field(min_length=12)
    current_cash_balance: float = Field(ge=0)
    restricted_cash: float = Field(default=0, ge=0)
    unused_credit: float = Field(default=0, ge=0)
    minimum_cash_balance: float = Field(gt=0)
    planned_capex_3m: list[float] = Field(min_length=3, max_length=3)
    debt_service_3m: list[float] = Field(min_length=3, max_length=3)
    confirmed_extra_inflows_3m: list[float] = Field(
        default_factory=lambda: [0.0, 0.0, 0.0], min_length=3, max_length=3
    )
    stress_inflow_decline: float = Field(default=0.15, ge=0, le=0.8)
    stress_outflow_increase: float = Field(default=0.10, ge=0, le=0.8)

    @model_validator(mode="after")
    def validate_history(self) -> "CashGapForecastRequest":
        months = [item.month for item in self.history]
        if months != sorted(months):
            raise ValueError("history 必须按月份升序排列")
        if len(months) != len(set(months)):
            raise ValueError("history 中月份不得重复")
        if any(month > self.snapshot_date for month in months):
            raise ValueError("历史月份不得晚于 snapshot_date")
        if self.restricted_cash > self.current_cash_balance:
            raise ValueError("受限资金不能大于当前现金余额")
        for values in (
            self.planned_capex_3m,
            self.debt_service_3m,
            self.confirmed_extra_inflows_3m,
        ):
            if any(value < 0 for value in values):
                raise ValueError("未来计划金额不得为负数")
        return self


class CashGapMonthForecast(BaseModel):
    forecast_month: date
    p50_operating_inflow: float
    p50_operating_outflow: float
    p50_ending_cash: float
    p50_funding_gap: float
    p90_operating_inflow: float
    p90_operating_outflow: float
    p90_ending_cash: float
    p90_funding_gap: float
    planned_capex: float
    debt_service: float


class CashGapForecastResult(BaseModel):
    merchant_id: str
    snapshot_date: date
    horizon_months: int = 3
    available_cash_at_snapshot: float
    minimum_cash_balance: float
    unused_credit: float
    forecasts: list[CashGapMonthForecast]
    max_p50_funding_gap: float
    max_p90_funding_gap: float
    first_p50_gap_month: date | None
    first_p90_gap_month: date | None
    p90_need_after_unused_credit: float
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    confidence: Literal["MEDIUM", "HIGH"]
    drivers: list[str]
    model_version: str = "cash_gap_damped_trend_v1"
