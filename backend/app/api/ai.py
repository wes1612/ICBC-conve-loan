"""Minimal synchronous AI endpoints for the competition MVP."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.ai import (
    AiReportSummary,
    AiRuntimeStatus,
    AssistantMessageRequest,
    AssistantReply,
    ReportSummaryRequest,
)
from app.services import ai_service
from app.settings import (
    ai_assistant_model,
    ai_is_configured,
    ai_provider,
    ai_report_model,
)


router = APIRouter(prefix="/api/v1", tags=["ai-explanations"])


@router.get("/ai/status", response_model=AiRuntimeStatus)
def ai_status() -> AiRuntimeStatus:
    provider = ai_provider()
    return AiRuntimeStatus(
        provider=provider,
        assistant_model=ai_assistant_model(),
        report_model=ai_report_model(),
        configured=ai_is_configured(),
        inference_mode="local_fine_tuned" if provider == "local" else "hosted_api",
    )


def _translate_ai_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ai_service.AiNotConfiguredError):
        return HTTPException(status_code=503, detail=str(exc))
    if isinstance(exc, ai_service.AiOutputValidationError):
        return HTTPException(status_code=502, detail=ai_service.INVALID_OUTPUT_MESSAGE)
    return HTTPException(status_code=502, detail=str(exc) or ai_service.UNAVAILABLE_MESSAGE)


@router.post("/assistant/messages", response_model=AssistantReply)
def assistant_message(request: AssistantMessageRequest) -> AssistantReply:
    """Answer a bounded question about the current five-step workflow."""

    try:
        return ai_service.answer_workflow_question(request)
    except (
        ai_service.AiNotConfiguredError,
        ai_service.AiGenerationError,
        ai_service.AiOutputValidationError,
    ) as exc:
        raise _translate_ai_error(exc) from exc


@router.post("/ai/report-summary", response_model=AiReportSummary)
def report_summary(request: ReportSummaryRequest) -> AiReportSummary:
    """Explain an existing FullAnalysisResult without changing its decisions."""

    try:
        return ai_service.generate_report_summary(request.analysis)
    except (
        ai_service.AiNotConfiguredError,
        ai_service.AiGenerationError,
        ai_service.AiOutputValidationError,
    ) as exc:
        raise _translate_ai_error(exc) from exc
