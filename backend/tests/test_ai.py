from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import pytest

from app.main import app
from app.schemas.ai import AI_DISCLAIMER, AiReportSummary, AssistantReply
from app.schemas.full_analysis import FullAnalysisResult
from app.services import ai_service


REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = REPO_ROOT / "docs" / "api_examples"
ANALYSIS = FullAnalysisResult.model_validate_json(
    (EXAMPLES / "full_analysis_review_response.json").read_text(encoding="utf-8")
)


def _request(method: str, url: str, *, json_body: dict | None = None) -> httpx.Response:
    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            return await client.request(method, url, json=json_body)

    return asyncio.run(send())


def _assistant_payload() -> dict:
    return {
        "message": "为什么需要这些材料？",
        "current_step": "data",
        "context": {
            "merchant_id": "M005",
            "identity_verified": True,
            "materials": [],
            "authorized_sources": [],
            "consent_confirmed": False,
            "analysis": None,
        },
        "history": [],
    }


def _valid_summary(**changes: object) -> AiReportSummary:
    values: dict[str, object] = {
        "overall_summary": "现有结构化结果包含需要人工核查的风险信号。",
        "positive_factors": ["经营数据中存在可解释的有利因素。"],
        "risk_factors": ["审核门控要求进一步核查。"],
        "cash_gap_interpretation": "资金缺口模块结果应结合现有驱动因素理解。",
        "recommended_actions": ["按照现有审核规则补充核查。"],
        "evidence_refs": ["SCORE", "CASH-GAP"],
        "disclaimer": AI_DISCLAIMER,
    }
    values.update(changes)
    return AiReportSummary.model_validate(values)


def test_assistant_endpoint_degrades_when_key_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ICBC_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = _request(
        "POST", "/api/v1/assistant/messages", json_body=_assistant_payload()
    )

    assert response.status_code == 503
    assert response.json()["detail"] == ai_service.UNAVAILABLE_MESSAGE


def test_assistant_endpoint_returns_only_real_service_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = AssistantReply(
        answer="现金流、财务和纳税材料用于现有规则计算与交叉核验。",
        evidence_refs=["STEP-DATA-PURPOSE", "MAT-REQ-CASHFLOW"],
        should_escalate=False,
    )
    monkeypatch.setattr(
        ai_service, "answer_workflow_question", lambda request: expected
    )

    response = _request(
        "POST", "/api/v1/assistant/messages", json_body=_assistant_payload()
    )

    assert response.status_code == 200
    assert response.json() == expected.model_dump(mode="json")


def test_report_summary_endpoint_uses_existing_full_analysis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = _valid_summary()
    monkeypatch.setattr(ai_service, "generate_report_summary", lambda analysis: expected)

    response = _request(
        "POST",
        "/api/v1/ai/report-summary",
        json_body={"analysis": ANALYSIS.model_dump(mode="json")},
    )

    assert response.status_code == 200
    assert response.json() == expected.model_dump(mode="json")


def test_report_summary_rejects_unknown_evidence_reference() -> None:
    with pytest.raises(ai_service.AiOutputValidationError, match="unsupported evidence"):
        ai_service.validate_report_summary(
            _valid_summary(evidence_refs=["MADE-UP-REF"]), ANALYSIS
        )


def test_report_summary_rejects_invented_number() -> None:
    with pytest.raises(ai_service.AiOutputValidationError, match="numeric"):
        ai_service.validate_report_summary(
            _valid_summary(overall_summary="建议额度是 999999 元。"), ANALYSIS
        )


def test_report_summary_rejects_lending_commitment() -> None:
    with pytest.raises(ai_service.AiOutputValidationError, match="commitment"):
        ai_service.validate_report_summary(
            _valid_summary(overall_summary="银行一定会放款。"), ANALYSIS
        )


def test_ai_failure_does_not_break_existing_health_or_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ICBC_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    unavailable = _request(
        "POST",
        "/api/v1/ai/report-summary",
        json_body={"analysis": ANALYSIS.model_dump(mode="json")},
    )
    health = _request("GET", "/health")

    assert unavailable.status_code == 503
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
