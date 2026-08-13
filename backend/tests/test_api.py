from __future__ import annotations

import asyncio
import base64
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

def _materials(merchant_id: str) -> list[dict]:
    return [
        {
            "material_id": f"MAT-{merchant_id}-{group.upper()}-{index:08d}",
            "merchant_id": merchant_id,
            "group": group,
            "file_name": f"{merchant_id}_{group}.pdf",
            "media_type": "application/pdf",
            "size_bytes": 128,
            "sha256": f"{index:064x}",
            "parse_status": "PARSED",
            "simulated": True,
            "completeness_score": 95,
            "period_months": 12 if group in {"cashflow", "tax"} else None,
            "subject_match": True,
            "extracted_metrics": [{"label": "文件校验", "value": "已通过"}],
            "findings": ["测试材料已解析"],
            "warnings": [],
        }
        for index, group in enumerate(
            ["license", "cashflow", "statement", "tax", "plan"], start=1
        )
    ]


APPLICATION = {
    "social_credit_code": "91310000MA1DEMO005",
    "province": "上海市",
    "city": "上海市",
    "operating_address": "上海市示范区惠民路88号",
    "legal_name": "李女士",
    "legal_phone": "13800000001",
    "legal_id_number": "310101199001010011",
    "contact_name": "李女士",
    "contact_phone": "13800000001",
    "contact_id_number": "310101199001010011",
    "identity_verified": True,
    "uploaded_data_groups": ["cashflow", "statement", "tax", "plan"],
    "authorized_sources": ["bank", "meituan", "enterprise"],
    "consent_confirmed": True,
    "consented_at": "2026-08-11T08:00:00Z",
    "materials": _materials("M005"),
}


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
        "application": APPLICATION,
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
    assert payload["overall_decision"] == "MANUAL_REVIEW"
    assert payload["module_states"] == {
        "score": "READY",
        "anomaly": "READY",
        "cash_gap": "READY",
    }
    assert len(payload["material_evidence"]) == 5


def test_material_parse_endpoint_validates_and_returns_evidence() -> None:
    content = b"%PDF-1.4\ncontest demo\n%%EOF"
    response = _request(
        "POST",
        "/api/v1/materials/parse",
        json_body={
            "merchant_id": "M005",
            "group": "cashflow",
            "file_name": "M005_cashflow.pdf",
            "media_type": "application/pdf",
            "size_bytes": len(content),
            "content_base64": base64.b64encode(content).decode("ascii"),
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["parse_status"] == "PARSED"
    assert payload["completeness_score"] == 82
    assert payload["subject_match"] is False
    assert payload["simulated"] is True


def test_demo_material_download_returns_real_workbook() -> None:
    response = _request("GET", "/api/v1/materials/demo/M001/cashflow")
    assert response.status_code == 200
    assert response.content.startswith(b"PK")
    assert "M001_cashflow_12m.xlsx" in response.headers["content-disposition"]


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
