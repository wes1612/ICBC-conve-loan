from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.full_analysis import FullAnalysisRequest
from app.services.full_analysis_service import run_full_analysis


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
MERCHANTS = json.loads(
    (BACKEND_ROOT / "tests" / "fixtures" / "merchants.json").read_text(
        encoding="utf-8"
    )
)
TRANSACTIONS = json.loads(
    (REPO_ROOT / "data" / "ml_simulated" / "transactions.json").read_text(
        encoding="utf-8"
    )
)
CASHFLOWS = json.loads(
    (REPO_ROOT / "data" / "ml_simulated" / "cashflow_monthly.json").read_text(
        encoding="utf-8"
    )
)


def _full_payload(index: int) -> dict:
    merchant = {**MERCHANTS[index]["input"], "profile": "v5_current"}
    return {
        "merchant": merchant,
        "anomaly": TRANSACTIONS[index]["input"],
        "cash_gap": CASHFLOWS[index]["input"],
    }


def test_full_analysis_combines_normal_merchant_modules() -> None:
    result = run_full_analysis(FullAnalysisRequest.model_validate(_full_payload(0)))
    assert result.merchant_id == "M001"
    assert result.overall_risk == "LOW"
    assert result.module_states.anomaly == "READY"
    assert result.module_states.cash_gap == "READY"
    assert result.data_warnings == []
    assert result.anomaly is not None
    assert result.cash_gap is not None


def test_full_analysis_routes_high_anomaly_to_manual_review() -> None:
    result = run_full_analysis(FullAnalysisRequest.model_validate(_full_payload(4)))
    assert result.overall_risk == "MANUAL_REVIEW"
    assert result.score.review_required is True
    assert result.anomaly is not None and result.anomaly.risk_level == "HIGH"
    assert result.cash_gap is not None and result.cash_gap.risk_level == "MEDIUM"


def test_full_analysis_allows_partial_data_with_explicit_warnings() -> None:
    request = FullAnalysisRequest.model_validate({"merchant": _full_payload(0)["merchant"]})
    result = run_full_analysis(request)
    assert result.overall_risk == "LOW"
    assert result.module_states.anomaly == "NOT_PROVIDED"
    assert result.module_states.cash_gap == "NOT_PROVIDED"
    assert result.anomaly is None
    assert result.cash_gap is None
    assert len(result.data_warnings) == 2


def test_full_analysis_rejects_cross_merchant_data() -> None:
    payload = _full_payload(0)
    payload["anomaly"] = TRANSACTIONS[1]["input"]
    with pytest.raises(ValidationError, match="必须与"):
        FullAnalysisRequest.model_validate(payload)

