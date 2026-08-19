"""Build the bounded structured context used by report-writing models."""

from __future__ import annotations

from typing import Any

from app.schemas.full_analysis import FullAnalysisResult


def build_report_context(analysis: FullAnalysisResult) -> dict[str, Any]:
    """Keep decision evidence while removing bulky features not used in prose."""

    score = analysis.score
    context: dict[str, Any] = {
        "merchant_id": analysis.merchant_id,
        "generated_at": analysis.generated_at.isoformat(),
        "overall_risk": analysis.overall_risk,
        "overall_decision": analysis.overall_decision,
        "module_states": analysis.module_states.model_dump(mode="json"),
        "data_warnings": analysis.data_warnings,
        "score": {
            "merchant_name": score.merchant_name,
            "score_version": score.score_version,
            "dimensions": score.dimensions.model_dump(mode="json"),
            "operating_credit_score": score.operating_credit_score,
            "credit_grade": score.credit_grade,
            "risk_band": score.risk_band,
            "confidence": score.confidence,
            "decision": score.decision,
            "review_required": score.review_required,
            "review_rules": [item.model_dump(mode="json") for item in score.review_rules],
            "positive_reasons": score.positive_reasons,
            "negative_reasons": score.negative_reasons,
            "limit": score.limit.model_dump(mode="json"),
        },
        "anomaly": None,
        "cash_gap": None,
        "material_evidence": [
            {
                "material_id": item.material_id,
                "group": item.group,
                "completeness_score": item.completeness_score,
                "subject_match": item.subject_match,
                "findings": item.findings,
                "warnings": item.warnings,
            }
            for item in analysis.material_evidence
        ],
        "api_version": analysis.api_version,
    }
    if analysis.anomaly:
        anomaly = analysis.anomaly
        context["anomaly"] = {
            "anomaly_score": anomaly.anomaly_score,
            "risk_level": anomaly.risk_level,
            "confidence": anomaly.confidence,
            "reason_codes": anomaly.reason_codes,
            "rule_hits": [
                {
                    "code": item.code,
                    "level": item.level,
                    "contribution": item.contribution,
                    "message": item.message,
                }
                for item in anomaly.rule_hits
            ],
            "model_version": anomaly.model_version,
        }
    if analysis.cash_gap:
        cash_gap = analysis.cash_gap
        context["cash_gap"] = {
            "snapshot_date": cash_gap.snapshot_date.isoformat(),
            "horizon_months": cash_gap.horizon_months,
            "available_cash_at_snapshot": cash_gap.available_cash_at_snapshot,
            "minimum_cash_balance": cash_gap.minimum_cash_balance,
            "unused_credit": cash_gap.unused_credit,
            "forecasts": [
                {
                    "forecast_month": item.forecast_month.isoformat(),
                    "p50_funding_gap": item.p50_funding_gap,
                    "p90_funding_gap": item.p90_funding_gap,
                    "planned_capex": item.planned_capex,
                    "debt_service": item.debt_service,
                }
                for item in cash_gap.forecasts
            ],
            "max_p50_funding_gap": cash_gap.max_p50_funding_gap,
            "max_p90_funding_gap": cash_gap.max_p90_funding_gap,
            "first_p50_gap_month": (
                cash_gap.first_p50_gap_month.isoformat()
                if cash_gap.first_p50_gap_month
                else None
            ),
            "first_p90_gap_month": (
                cash_gap.first_p90_gap_month.isoformat()
                if cash_gap.first_p90_gap_month
                else None
            ),
            "p90_need_after_unused_credit": cash_gap.p90_need_after_unused_credit,
            "risk_level": cash_gap.risk_level,
            "confidence": cash_gap.confidence,
            "drivers": cash_gap.drivers,
            "model_version": cash_gap.model_version,
        }
    return context
