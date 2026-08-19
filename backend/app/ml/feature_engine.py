"""从统一请求生成可审计的特征快照。"""

from __future__ import annotations

import math
import re
import statistics
import unicodedata

from app.ml.config import (
    COMPLETENESS_FIELD_COUNT,
    INDUSTRY_MONTHLY_CAPACITY_PER_EMPLOYEE,
    REVIEW_ORDER_RATIO_THRESHOLD,
)
from app.schemas.analysis import FeatureSnapshot
from app.schemas.merchant import MerchantAnalysisRequest


def _mean_optional(values: list[float | None]) -> float | None:
    valid = [float(value) for value in values if value is not None]
    return statistics.fmean(valid) if valid else None


def _safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def _pearson(left: list[float], right: list[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    left_mean = statistics.fmean(left)
    right_mean = statistics.fmean(right)
    left_delta = [value - left_mean for value in left]
    right_delta = [value - right_mean for value in right]
    denominator = math.sqrt(
        sum(value * value for value in left_delta)
        * sum(value * value for value in right_delta)
    )
    if denominator == 0:
        return None
    return sum(a * b for a, b in zip(left_delta, right_delta, strict=True)) / denominator


def _normalize_subject(value: str | None) -> str | None:
    if not value:
        return None
    normalized = unicodedata.normalize("NFKC", value)
    return re.sub(r"\s+", "", normalized).casefold()


def _subject_consistency(request: MerchantAnalysisRequest) -> str:
    structural = request.structural
    normalized = [
        _normalize_subject(structural.license_subject),
        _normalize_subject(structural.account_holder),
        _normalize_subject(structural.invoice_issuer),
    ]
    if any(value is None for value in normalized):
        return "待补充"
    return "通过" if len(set(normalized)) == 1 else "异常"


def build_features(request: MerchantAnalysisRequest) -> FeatureSnapshot:
    structural = request.structural
    unstructured = request.unstructured

    receipts_12 = [float(value) for value in structural.monthly_receipts[-12:]]
    receipts_6 = receipts_12[-6:]
    orders_12 = [float(value) for value in structural.monthly_orders[-12:]]
    orders_6 = orders_12[-6:]
    redemption_6 = structural.monthly_redemption_rates[-6:]
    refund_6 = structural.monthly_refund_rates[-6:]

    receipts_total_6 = sum(receipts_6)
    receipts_total_12 = sum(receipts_12)
    average_receipt_6 = receipts_total_6 / len(receipts_6)
    active_months = sum(1 for value in receipts_6 if value > 0)

    receipt_mom_growth = _safe_ratio(receipts_6[-1], receipts_6[-2])
    if receipt_mom_growth is not None:
        receipt_mom_growth -= 1

    receipt_cagr = None
    if receipts_6[0] > 0 and receipts_6[-1] >= 0:
        receipt_cagr = (receipts_6[-1] / receipts_6[0]) ** (1 / 5) - 1

    receipt_volatility = None
    if average_receipt_6 > 0:
        receipt_volatility = statistics.pstdev(receipts_6) / average_receipt_6

    max_month_share = _safe_ratio(max(receipts_6), receipts_total_6)
    orders_total_6 = sum(orders_6)
    monthly_orders_6 = orders_total_6 / len(orders_6)
    order_growth_6 = _safe_ratio(orders_6[-1], orders_6[0])
    if order_growth_6 is not None:
        order_growth_6 -= 1

    redemption_rate = _mean_optional(redemption_6)
    refund_rate = _mean_optional(refund_6)
    effective_orders = None
    if redemption_rate is not None and refund_rate is not None:
        effective_orders = orders_total_6 * redemption_rate * (1 - refund_rate)

    estimated_ticket = _safe_ratio(receipts_total_6, effective_orders)

    cashflow_margin = None
    if structural.operating_cash_inflow_6m not in (None, 0):
        cashflow_margin = (
            structural.operating_cash_inflow_6m
            - (structural.operating_cash_outflow_6m or 0)
        ) / structural.operating_cash_inflow_6m

    debt_ratio = _safe_ratio(structural.total_liabilities, structural.total_assets)
    current_ratio = _safe_ratio(structural.current_assets, structural.current_liabilities)

    invoice_receipt_diff = None
    if structural.sales_invoice_amount_12m is not None and receipts_total_12 > 0:
        invoice_receipt_diff = abs(
            structural.sales_invoice_amount_12m - receipts_total_12
        ) / receipts_total_12

    cashflow_receipt_diff = None
    if structural.operating_cash_inflow_6m is not None and receipts_total_6 > 0:
        cashflow_receipt_diff = abs(
            structural.operating_cash_inflow_6m - receipts_total_6
        ) / receipts_total_6

    valid_invoice_ratio = _safe_ratio(
        structural.valid_invoice_count,
        structural.invoice_count,
    )
    correlation = _pearson(orders_6, receipts_6)

    subject_consistency = _subject_consistency(request)
    structured_inconsistency = structural.raw_inconsistency_count
    if subject_consistency == "异常":
        structured_inconsistency += 1

    review_order_ratio = _safe_ratio(unstructured.valid_review_count, effective_orders)
    final_inconsistency = structured_inconsistency
    if review_order_ratio is not None and review_order_ratio > REVIEW_ORDER_RATIO_THRESHOLD:
        final_inconsistency += 1

    completeness = (
        COMPLETENESS_FIELD_COUNT - structural.missing_key_field_count
    ) / COMPLETENESS_FIELD_COUNT

    unit_capacity = INDUSTRY_MONTHLY_CAPACITY_PER_EMPLOYEE.get(structural.industry)
    capacity_utilization = None
    if unit_capacity:
        capacity_utilization = monthly_orders_6 / (
            structural.employee_count * unit_capacity
        )

    peak_growth = structural.peak_season_order_growth
    if peak_growth is None and len(orders_12) >= 7 and orders_12[-7] != 0:
        peak_growth = orders_12[-1] / orders_12[-7] - 1

    return FeatureSnapshot(
        receipts_6m=receipts_total_6,
        receipts_12m=receipts_total_12,
        average_receipt_6m=average_receipt_6,
        receipt_mom_growth=receipt_mom_growth,
        receipt_cagr_6m=receipt_cagr,
        receipt_volatility=receipt_volatility,
        max_month_receipt_share=max_month_share,
        active_months_6m=active_months,
        operating_cashflow_margin_6m=cashflow_margin,
        debt_ratio=debt_ratio,
        current_ratio=current_ratio,
        platform_orders_6m=orders_total_6,
        platform_order_growth_6m=order_growth_6,
        redemption_rate_6m=redemption_rate,
        refund_rate_6m=refund_rate,
        effective_orders_6m=effective_orders,
        estimated_ticket_6m=estimated_ticket,
        invoice_receipt_diff=invoice_receipt_diff,
        cashflow_receipt_diff=cashflow_receipt_diff,
        order_receipt_correlation=correlation,
        valid_invoice_ratio=valid_invoice_ratio,
        subject_consistency=subject_consistency,
        data_completeness=completeness,
        structured_inconsistency_count=structured_inconsistency,
        final_inconsistency_count=final_inconsistency,
        review_order_ratio=review_order_ratio,
        monthly_orders_6m=monthly_orders_6,
        capacity_utilization=capacity_utilization,
        peak_season_order_growth=peak_growth,
    )

