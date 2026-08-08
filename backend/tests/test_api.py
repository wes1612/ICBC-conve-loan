from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

import httpx

from app.main import app

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "merchants.json"
MERCHANT_1 = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))[0]["input"]
MERCHANT_5 = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))[4]["input"]
SIMULATED_DATA = Path(__file__).resolve().parents[2] / "data" / "ml_simulated"
TRANSACTION_5 = json.loads(
    (SIMULATED_DATA / "transactions.json").read_text(encoding="utf-8")
)[4]["input"]
CASHFLOW_3 = json.loads(
    (SIMULATED_DATA / "cashflow_monthly.json").read_text(encoding="utf-8")
)[2]["input"]


def _request(
    method: str,
    url: str,
    *,
    json_body: dict | None = None,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            return await client.request(method, url, json=json_body, headers=headers)

    return asyncio.run(send())


def test_health_endpoint() -> None:
    response = _request("GET", "/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_endpoint() -> None:
    response = _request("POST", "/api/v1/analyze", json_body=MERCHANT_1)
    assert response.status_code == 200
    payload = response.json()
    assert payload["operating_credit_score"] == 90.6
    assert payload["limit"]["recommended_limit"] == 438042
    assert payload["pd_12m"] is None


def test_analyze_endpoint_uses_v5_profile_from_request_body() -> None:
    request = {**MERCHANT_5, "profile": "v5_current"}
    response = _request("POST", "/api/v1/analyze", json_body=request)
    assert response.status_code == 200
    payload = response.json()
    assert payload["profile"] == "v5_current"
    assert payload["operating_credit_score"] == 61.1
    assert payload["credit_grade"] == "D"
    assert payload["review_required"] is True
    assert "V09" in {rule["code"] for rule in payload["review_rules"]}


def test_ml_score_alias_endpoint() -> None:
    response = _request("POST", "/api/v1/ml/score", json_body=MERCHANT_1)
    assert response.status_code == 200
    assert response.json()["operating_credit_score"] == 90.6


def test_anomaly_endpoint_returns_evidence() -> None:
    response = _request("POST", "/api/v1/ml/anomalies", json_body=TRANSACTION_5)
    assert response.status_code == 200
    payload = response.json()
    assert payload["risk_level"] == "HIGH"
    assert payload["anomaly_score"] == 100
    assert payload["evidence_transaction_ids"]


def test_cash_gap_endpoint_returns_three_month_scenarios() -> None:
    response = _request("POST", "/api/v1/ml/cash-gap", json_body=CASHFLOW_3)
    assert response.status_code == 200
    payload = response.json()
    assert payload["risk_level"] == "HIGH"
    assert len(payload["forecasts"]) == 3
    assert payload["max_p90_funding_gap"] >= payload["max_p50_funding_gap"]


def test_full_analysis_endpoint_returns_all_modules() -> None:
    request = {
        "merchant": {**MERCHANT_5, "profile": "v5_current"},
        "anomaly": TRANSACTION_5,
        "cash_gap": json.loads(
            (SIMULATED_DATA / "cashflow_monthly.json").read_text(encoding="utf-8")
        )[4]["input"],
    }
    response = _request("POST", "/api/v1/ml/full-analysis", json_body=request)
    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_risk"] == "MANUAL_REVIEW"
    assert payload["module_states"] == {
        "score": "READY",
        "anomaly": "READY",
        "cash_gap": "READY",
    }


def test_local_frontend_origin_passes_cors_preflight() -> None:
    response = _request(
        "OPTIONS",
        "/api/v1/ml/full-analysis",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
