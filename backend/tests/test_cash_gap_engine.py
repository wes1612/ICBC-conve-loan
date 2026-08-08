from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.ml.cash_gap_engine import forecast_cash_gap
from app.schemas.cash_gap import CashGapForecastRequest


DATA_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "ml_simulated"
    / "cashflow_monthly.json"
)
CASES = json.loads(DATA_PATH.read_text(encoding="utf-8"))


def _results_by_merchant() -> dict[str, object]:
    return {
        case["input"]["merchant_id"]: forecast_cash_gap(
            CashGapForecastRequest.model_validate(case["input"])
        )
        for case in CASES
    }


def test_cash_gap_scenarios_distinguish_liquidity_profiles() -> None:
    results = _results_by_merchant()
    assert results["M001"].risk_level == "LOW"
    assert results["M001"].max_p90_funding_gap == 0
    assert results["M002"].risk_level == "HIGH"
    assert results["M002"].max_p50_funding_gap > 0
    assert results["M003"].risk_level == "HIGH"
    assert results["M003"].first_p50_gap_month is not None
    assert results["M005"].risk_level == "MEDIUM"
    assert results["M005"].max_p50_funding_gap == 0
    assert results["M005"].max_p90_funding_gap > 0


def test_p90_gap_is_not_lower_than_p50_gap() -> None:
    for result in _results_by_merchant().values():
        assert len(result.forecasts) == 3
        assert result.max_p90_funding_gap >= result.max_p50_funding_gap
        assert all(
            month.p90_funding_gap >= month.p50_funding_gap
            for month in result.forecasts
        )


def test_cash_gap_request_rejects_unsorted_history() -> None:
    payload = json.loads(json.dumps(CASES[0]["input"], ensure_ascii=False))
    payload["history"][0], payload["history"][1] = (
        payload["history"][1],
        payload["history"][0],
    )
    with pytest.raises(ValidationError, match="升序"):
        CashGapForecastRequest.model_validate(payload)

