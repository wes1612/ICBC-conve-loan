"""Contracts for the two deliberately limited LLM workflows."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.full_analysis import AuthorizedSource, FullAnalysisResult
from app.schemas.material import MaterialGroup


WorkflowStep = Literal["identity", "verify", "data", "authorize", "results"]
AI_DISCLAIMER = "AI仅解释既有分析结果，不参与评分与授信决策。"


class AssistantHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1200)


class AssistantMaterialStatus(BaseModel):
    material_id: str = Field(min_length=1, max_length=120)
    group: MaterialGroup
    completeness_score: int = Field(ge=0, le=100)
    subject_match: bool
    warnings: list[str] = Field(default_factory=list, max_length=6)


class AssistantWorkflowContext(BaseModel):
    merchant_id: str | None = Field(default=None, max_length=80)
    identity_verified: bool = False
    materials: list[AssistantMaterialStatus] = Field(default_factory=list, max_length=12)
    authorized_sources: list[AuthorizedSource] = Field(default_factory=list, max_length=12)
    consent_confirmed: bool = False
    analysis: FullAnalysisResult | None = None


class AssistantMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    current_step: WorkflowStep
    context: AssistantWorkflowContext
    history: list[AssistantHistoryMessage] = Field(default_factory=list, max_length=8)


class AssistantReply(BaseModel):
    answer: str = Field(
        min_length=1,
        max_length=1200,
        description=(
            "Readable Chinese explanation with 【简要结论】 and 【要点】 sections; "
            "key points use lines beginning with '- '."
        ),
    )
    evidence_refs: list[str] = Field(default_factory=list, max_length=8)
    should_escalate: bool = False


class ReportSummaryRequest(BaseModel):
    analysis: FullAnalysisResult


class AiReportSummary(BaseModel):
    overall_summary: str = Field(min_length=1, max_length=800)
    positive_factors: list[str] = Field(min_length=1, max_length=6)
    risk_factors: list[str] = Field(min_length=1, max_length=8)
    cash_gap_interpretation: str = Field(min_length=1, max_length=600)
    recommended_actions: list[str] = Field(min_length=1, max_length=6)
    evidence_refs: list[str] = Field(min_length=1, max_length=12)
    disclaimer: Literal["AI仅解释既有分析结果，不参与评分与授信决策。"]


class AiRuntimeStatus(BaseModel):
    provider: Literal["deepseek", "openai", "local"]
    assistant_model: str
    report_model: str
    configured: bool
    inference_mode: Literal["hosted_api", "local_fine_tuned"]
