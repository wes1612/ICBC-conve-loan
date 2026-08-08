from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.ml.anomaly_engine import analyze_transactions
from app.schemas.anomaly import AnomalyAnalysisRequest


DATA_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "ml_simulated" / "transactions.json"
)
CASES = json.loads(DATA_PATH.read_text(encoding="utf-8"))


def _results_by_merchant() -> dict[str, object]:
    return {
        case["input"]["merchant_id"]: analyze_transactions(
            AnomalyAnalysisRequest.model_validate(case["input"])
        )
        for case in CASES
    }


def test_five_simulated_merchants_have_expected_anomaly_ordering() -> None:
    results = _results_by_merchant()
    assert results["M001"].anomaly_score == 0
    assert results["M001"].risk_level == "LOW"
    assert results["M003"].anomaly_score == 20
    assert results["M003"].risk_level == "MEDIUM"
    assert results["M005"].anomaly_score == 100
    assert results["M005"].risk_level == "HIGH"


def test_m005_returns_explainable_rules_and_evidence() -> None:
    result = _results_by_merchant()["M005"]
    expected = {
        "REPEATED_ROUND_AMOUNT",
        "OFF_HOURS_CONCENTRATION",
        "COUNTERPARTY_CONCENTRATION",
        "RAPID_IN_OUT_ROUNDTRIP",
        "HIGH_REFUND_REVERSAL",
        "MISSING_ORDER_LINK",
    }
    assert expected.issubset(result.reason_codes)
    assert result.evidence_transaction_ids
    assert all(hit.evidence_transaction_ids for hit in result.rule_hits)


def test_anomaly_request_rejects_future_transaction() -> None:
    payload = json.loads(json.dumps(CASES[0]["input"], ensure_ascii=False))
    payload["as_of_time"] = "2025-01-01T00:00:00"
    with pytest.raises(ValidationError, match="不得晚于"):
        AnomalyAnalysisRequest.model_validate(payload)

