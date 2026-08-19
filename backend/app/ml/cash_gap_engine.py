"""阻尼趋势与压力情景结合的三个月资金缺口预测基线。"""

from __future__ import annotations

import statistics
from datetime import date

from app.schemas.cash_gap import (
    CashGapForecastRequest,
    CashGapForecastResult,
    CashGapMonthForecast,
)


DAMPING_FACTOR = 0.75
P90_Z_VALUE = 1.28


def _next_month(value: date, offset: int) -> date:
    month_index = value.year * 12 + value.month - 1 + offset
    return date(month_index // 12, month_index % 12 + 1, 1)


def _linear_slope(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    x_mean = (len(values) - 1) / 2
    y_mean = statistics.fmean(values)
    denominator = sum((index - x_mean) ** 2 for index in range(len(values)))
    if denominator == 0:
        return 0.0
    return sum(
        (index - x_mean) * (value - y_mean)
        for index, value in enumerate(values)
    ) / denominator


def _forecast_path(values: list[float], horizon: int = 3) -> tuple[list[float], float]:
    recent = values[-6:]
    base = sum(
        weight * value
        for weight, value in zip((0.2, 0.3, 0.5), recent[-3:], strict=True)
    )
    slope = _linear_slope(recent)
    forecasts: list[float] = []
    for step in range(1, horizon + 1):
        damped_change = slope * sum(DAMPING_FACTOR**power for power in range(1, step + 1))
        forecasts.append(max(0.0, base + damped_change))
    return forecasts, slope


def _round_money(value: float) -> float:
    return round(value, 2)


def forecast_cash_gap(request: CashGapForecastRequest) -> CashGapForecastResult:
    inflow_history = [item.operating_inflow for item in request.history]
    outflow_history = [item.operating_outflow for item in request.history]
    p50_inflows, inflow_slope = _forecast_path(inflow_history)
    p50_outflows, outflow_slope = _forecast_path(outflow_history)

    inflow_sigma = statistics.pstdev(inflow_history[-6:])
    outflow_sigma = statistics.pstdev(outflow_history[-6:])
    p50_cash = request.current_cash_balance - request.restricted_cash
    p90_cash = p50_cash
    forecasts: list[CashGapMonthForecast] = []

    for index in range(3):
        confirmed_inflow = request.confirmed_extra_inflows_3m[index]
        p50_inflow = p50_inflows[index] + confirmed_inflow
        p50_outflow = p50_outflows[index]
        p90_inflow = max(
            0.0,
            (p50_inflows[index] - P90_Z_VALUE * inflow_sigma)
            * (1 - request.stress_inflow_decline),
        ) + confirmed_inflow
        p90_outflow = (
            p50_outflows[index] + P90_Z_VALUE * outflow_sigma
        ) * (1 + request.stress_outflow_increase)

        capex = request.planned_capex_3m[index]
        debt_service = request.debt_service_3m[index]
        p50_cash = p50_cash + p50_inflow - p50_outflow - capex - debt_service
        p90_cash = p90_cash + p90_inflow - p90_outflow - capex - debt_service
        p50_gap = max(0.0, request.minimum_cash_balance - p50_cash)
        p90_gap = max(0.0, request.minimum_cash_balance - p90_cash)

        forecasts.append(
            CashGapMonthForecast(
                forecast_month=_next_month(request.snapshot_date, index + 1),
                p50_operating_inflow=_round_money(p50_inflow),
                p50_operating_outflow=_round_money(p50_outflow),
                p50_ending_cash=_round_money(p50_cash),
                p50_funding_gap=_round_money(p50_gap),
                p90_operating_inflow=_round_money(p90_inflow),
                p90_operating_outflow=_round_money(p90_outflow),
                p90_ending_cash=_round_money(p90_cash),
                p90_funding_gap=_round_money(p90_gap),
                planned_capex=_round_money(capex),
                debt_service=_round_money(debt_service),
            )
        )

    max_p50_gap = max(item.p50_funding_gap for item in forecasts)
    max_p90_gap = max(item.p90_funding_gap for item in forecasts)
    first_p50 = next(
        (item.forecast_month for item in forecasts if item.p50_funding_gap > 0), None
    )
    first_p90 = next(
        (item.forecast_month for item in forecasts if item.p90_funding_gap > 0), None
    )
    need_after_credit = max(0.0, max_p90_gap - request.unused_credit)

    if max_p50_gap > 0 or need_after_credit > request.minimum_cash_balance:
        risk_level = "HIGH"
    elif max_p90_gap > 0:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    drivers: list[str] = []
    if inflow_slope < 0:
        drivers.append("近6个月经营现金流入呈下降趋势")
    if outflow_slope > 0:
        drivers.append("近6个月经营现金流出呈上升趋势")
    if sum(request.planned_capex_3m) > statistics.fmean(inflow_history[-3:]):
        drivers.append("未来3个月计划资本开支较高")
    if sum(request.debt_service_3m) > 0:
        drivers.append("未来3个月存在还本付息安排")
    if max_p50_gap > 0:
        drivers.append("基准情景已出现最低安全现金缺口")
    elif max_p90_gap > 0:
        drivers.append("压力情景出现最低安全现金缺口")
    if not drivers:
        drivers.append("基准与压力情景下现金缓冲均充足")

    return CashGapForecastResult(
        merchant_id=request.merchant_id,
        snapshot_date=request.snapshot_date,
        available_cash_at_snapshot=_round_money(
            request.current_cash_balance - request.restricted_cash
        ),
        minimum_cash_balance=_round_money(request.minimum_cash_balance),
        unused_credit=_round_money(request.unused_credit),
        forecasts=forecasts,
        max_p50_funding_gap=_round_money(max_p50_gap),
        max_p90_funding_gap=_round_money(max_p90_gap),
        first_p50_gap_month=first_p50,
        first_p90_gap_month=first_p90,
        p90_need_after_unused_credit=_round_money(need_after_credit),
        risk_level=risk_level,  # type: ignore[arg-type]
        confidence="HIGH" if len(request.history) >= 18 else "MEDIUM",
        drivers=drivers[:5],
    )
