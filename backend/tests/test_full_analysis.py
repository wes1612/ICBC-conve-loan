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


def _application(merchant_id: str) -> dict:
    return {
        "social_credit_code": f"91310000MA1DEMO{merchant_id[-3:]}",
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
        "materials": _materials(merchant_id),
    }


def _full_payload(index: int) -> dict:
    merchant = {**MERCHANTS[index]["input"], "profile": "v5_current"}
    return {
        "application": _application(merchant["merchant_id"]),
        "merchant": merchant,
        "anomaly": TRANSACTIONS[index]["input"],
        "cash_gap": CASHFLOWS[index]["input"],
    }


def test_full_analysis_combines_normal_merchant_modules() -> None:
    request = FullAnalysisRequest.model_validate(_full_payload(0))
    assert request.application.province == "上海市"
    assert request.application.legal_phone == "13800000001"
    assert request.application.contact_id_number == "310101199001010011"
    result = run_full_analysis(request)
    assert result.merchant_id == "M001"
    assert result.overall_risk == "LOW"
    assert result.overall_decision == "APPROVE"
    assert result.module_states.anomaly == "READY"
    assert result.module_states.cash_gap == "READY"
    assert result.data_warnings == []
    assert result.anomaly is not None
    assert result.cash_gap is not None


def test_full_analysis_routes_high_anomaly_to_manual_review() -> None:
    result = run_full_analysis(FullAnalysisRequest.model_validate(_full_payload(4)))
    assert result.overall_risk == "MANUAL_REVIEW"
    assert result.overall_decision == "MANUAL_REVIEW"
    assert result.score.review_required is True
    assert result.anomaly is not None and result.anomaly.risk_level == "HIGH"
    assert result.cash_gap is not None and result.cash_gap.risk_level == "MEDIUM"


def test_full_analysis_allows_partial_data_with_explicit_warnings() -> None:
    request = FullAnalysisRequest.model_validate(
        {
            "application": _application("M001"),
            "merchant": _full_payload(0)["merchant"],
        }
    )
    result = run_full_analysis(request)
    assert result.overall_risk == "LOW"
    assert result.module_states.anomaly == "NOT_PROVIDED"
    assert result.module_states.cash_gap == "NOT_PROVIDED"
    assert result.anomaly is None
    assert result.cash_gap is None
    assert len(result.data_warnings) == 2


def test_full_analysis_routes_high_cash_gap_to_manual_review() -> None:
    payload = _full_payload(0)
    payload["cash_gap"] = {**payload["cash_gap"]}
    payload["cash_gap"]["current_cash_balance"] = 1000
    payload["cash_gap"]["restricted_cash"] = 0
    payload["cash_gap"]["unused_credit"] = 0
    payload["cash_gap"]["minimum_cash_balance"] = 100000
    payload["cash_gap"]["planned_capex_3m"] = [300000, 300000, 300000]
    result = run_full_analysis(FullAnalysisRequest.model_validate(payload))
    assert result.score.decision == "APPROVE"
    assert result.cash_gap is not None and result.cash_gap.risk_level == "HIGH"
    assert result.overall_risk == "HIGH"
    assert result.overall_decision == "MANUAL_REVIEW"


def test_full_analysis_rejects_cross_merchant_data() -> None:
    payload = _full_payload(0)
    payload["anomaly"] = TRANSACTIONS[1]["input"]
    with pytest.raises(ValidationError, match="必须与"):
        FullAnalysisRequest.model_validate(payload)


def test_full_analysis_rejects_missing_consent() -> None:
    payload = _full_payload(0)
    payload["application"] = {
        **_application("M001"),
        "consent_confirmed": False,
    }
    with pytest.raises(ValidationError, match="授权"):
        FullAnalysisRequest.model_validate(payload)


def test_full_analysis_rejects_missing_parsed_material() -> None:
    payload = _full_payload(0)
    payload["application"]["materials"] = [
        material
        for material in payload["application"]["materials"]
        if material["group"] != "tax"
    ]
    with pytest.raises(ValidationError, match="已解析材料"):
        FullAnalysisRequest.model_validate(payload)

