from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import pytest

from app.main import app
from app.schemas.ai import AI_DISCLAIMER, AiReportSummary, AssistantReply
from app.schemas.full_analysis import FullAnalysisResult
from app.services import ai_service
from app.services import llm_provider


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
    monkeypatch.setenv("ICBC_AI_PROVIDER", "deepseek")
    monkeypatch.delenv("ICBC_AI_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("ICBC_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = _request(
        "POST", "/api/v1/assistant/messages", json_body=_assistant_payload()
    )

    assert response.status_code == 503
    assert response.json()["detail"] == ai_service.NOT_CONFIGURED_MESSAGE


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


def test_ai_status_reports_deepseek_without_exposing_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ICBC_AI_PROVIDER", "deepseek")
    monkeypatch.setenv("ICBC_AI_API_KEY", "must-not-leak")
    monkeypatch.setenv("ICBC_AI_MODEL", "deepseek-v4-flash")

    response = _request("GET", "/api/v1/ai/status")

    assert response.status_code == 200
    assert response.json() == {
        "provider": "deepseek",
        "assistant_model": "deepseek-v4-flash",
        "report_model": "deepseek-v4-flash",
        "configured": True,
        "inference_mode": "hosted_api",
    }
    assert "must-not-leak" not in response.text


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


def test_report_summary_accepts_equivalent_integer_and_decimal_format() -> None:
    ai_service.validate_report_summary(
        _valid_summary(cash_gap_interpretation="期初可用现金为 65000 元。"),
        ANALYSIS,
    )


def test_provider_applies_report_array_presentation_limits() -> None:
    payload = {"risk_factors": [f"风险{i}" for i in range(11)]}

    normalized = llm_provider._enforce_top_level_array_limits(
        payload, AiReportSummary
    )

    assert normalized["risk_factors"] == [f"风险{i}" for i in range(8)]


def test_report_summary_rejects_lending_commitment() -> None:
    with pytest.raises(ai_service.AiOutputValidationError, match="commitment"):
        ai_service.validate_report_summary(
            _valid_summary(overall_summary="银行一定会放款。"), ANALYSIS
        )


def test_assistant_reply_accepts_readable_evidence_based_structure() -> None:
    reply = AssistantReply(
        answer=(
            "【简要结论】\n这些材料用于规则计算和交叉核验。\n"
            "【要点】\n- 现金流材料应覆盖连续 12 个月。\n- 财务和纳税资料用于核对经营真实性。\n"
            "【下一步】\n- 按页面缺失提示补齐材料。"
        ),
        evidence_refs=["STEP-DATA-PURPOSE", "MAT-REQ-CASHFLOW"],
        should_escalate=False,
    )

    validated = ai_service.validate_assistant_reply(
        reply,
        allowed_refs={"STEP-DATA-PURPOSE", "MAT-REQ-CASHFLOW"},
        source_text='{"period_months":12}',
    )

    assert validated is reply


def test_assistant_reply_rejects_invented_number() -> None:
    reply = AssistantReply(
        answer="【简要结论】\n目前无法确认。\n【要点】\n- 建议额度为 999999 元。\n- 需要人工核对。",
        evidence_refs=["SCORE"],
        should_escalate=True,
    )

    with pytest.raises(ai_service.AiOutputValidationError, match="numeric"):
        ai_service.validate_assistant_reply(
            reply,
            allowed_refs={"SCORE"},
            source_text='{"suggested_limit":500000}',
        )


def test_assistant_reply_rejects_wall_of_text() -> None:
    reply = AssistantReply(
        answer="材料用于规则计算、真实性核查和资金缺口预测。",
        evidence_refs=["STEP-DATA-PURPOSE"],
        should_escalate=False,
    )

    with pytest.raises(ai_service.AiOutputValidationError, match="readable sections"):
        ai_service.validate_assistant_reply(
            reply,
            allowed_refs={"STEP-DATA-PURPOSE"},
            source_text="{}",
        )


def test_ai_failure_does_not_break_existing_health_or_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ICBC_AI_PROVIDER", "deepseek")
    monkeypatch.delenv("ICBC_AI_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
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


def test_deepseek_adapter_uses_json_mode_and_local_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeCompletions:
        def create(self, **kwargs: object) -> object:
            captured.update(kwargs)
            message = type("Message", (), {"content": AssistantReply(
                answer="请核对材料完整度。",
                evidence_refs=["STEP-DATA-PURPOSE"],
                should_escalate=False,
            ).model_dump_json()})()
            choice = type("Choice", (), {"message": message})()
            usage = type("Usage", (), {"prompt_tokens": 12, "completion_tokens": 8})()
            return type(
                "Response",
                (),
                {"id": "ds-test", "choices": [choice], "usage": usage},
            )()

    class FakeClient:
        def __init__(self, **kwargs: object) -> None:
            captured["client"] = kwargs
            self.chat = type("Chat", (), {"completions": FakeCompletions()})()

    monkeypatch.setenv("ICBC_AI_PROVIDER", "deepseek")
    monkeypatch.setenv("ICBC_AI_API_KEY", "test-key")
    monkeypatch.delenv("ICBC_AI_BASE_URL", raising=False)
    monkeypatch.setattr(llm_provider, "OpenAI", FakeClient)

    result = llm_provider.generate_structured(
        model="deepseek-v4-flash",
        messages=[
            {"role": "developer", "content": "回答问题"},
            {"role": "user", "content": "为什么需要材料？"},
        ],
        output_model=AssistantReply,
        max_output_tokens=256,
    )

    assert isinstance(result.parsed, AssistantReply)
    assert result.response_id == "ds-test"
    assert captured["response_format"] == {"type": "json_object"}
    assert captured["extra_body"] == {"thinking": {"type": "disabled"}}
    messages = captured["messages"]
    assert isinstance(messages, list)
    assert messages[0]["role"] == "system"
    assert "JSON Schema" in messages[0]["content"]
    client_options = captured["client"]
    assert isinstance(client_options, dict)
    assert client_options["base_url"] == "https://api.deepseek.com"
