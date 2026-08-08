"""聚合三个 ML 引擎，向前端返回一次性分析结果。"""

from __future__ import annotations

from datetime import datetime, timezone

from app.ml.anomaly_engine import analyze_transactions
from app.ml.cash_gap_engine import forecast_cash_gap
from app.schemas.full_analysis import (
    FullAnalysisRequest,
    FullAnalysisResult,
    ModuleStates,
)
from app.services.analysis_service import analyze_merchant


def _overall_risk(
    score_risk: str,
    review_required: bool,
    anomaly_risk: str | None,
    cash_gap_risk: str | None,
) -> str:
    if review_required or score_risk == "MANUAL_REVIEW" or anomaly_risk == "HIGH":
        return "MANUAL_REVIEW"
    if "HIGH" in {score_risk, cash_gap_risk}:
        return "HIGH"
    if "MEDIUM" in {score_risk, anomaly_risk, cash_gap_risk}:
        return "MEDIUM"
    return "LOW"


def run_full_analysis(request: FullAnalysisRequest) -> FullAnalysisResult:
    score = analyze_merchant(request.merchant)
    anomaly = analyze_transactions(request.anomaly) if request.anomaly else None
    cash_gap = forecast_cash_gap(request.cash_gap) if request.cash_gap else None

    warnings: list[str] = []
    if anomaly is None:
        warnings.append("未提供交易明细，异常交易模块未运行")
    if cash_gap is None:
        warnings.append("未提供月度现金流，资金缺口模块未运行")

    overall_risk = _overall_risk(
        score.risk_band,
        score.review_required,
        anomaly.risk_level if anomaly else None,
        cash_gap.risk_level if cash_gap else None,
    )
    return FullAnalysisResult(
        merchant_id=request.merchant.merchant_id,
        generated_at=datetime.now(timezone.utc),
        overall_risk=overall_risk,  # type: ignore[arg-type]
        module_states=ModuleStates(
            anomaly="READY" if anomaly else "NOT_PROVIDED",
            cash_gap="READY" if cash_gap else "NOT_PROVIDED",
        ),
        data_warnings=warnings,
        score=score,
        anomaly=anomaly,
        cash_gap=cash_gap,
    )

