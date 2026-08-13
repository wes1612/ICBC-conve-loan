"""申请材料上传与模拟解析的数据契约。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


MaterialGroup = Literal[
    "license",
    "cashflow",
    "statement",
    "tax",
    "plan",
    "asset",
]
MetricTone = Literal["NEUTRAL", "POSITIVE", "WARNING", "DANGER"]


class ExtractedMetric(BaseModel):
    label: str = Field(min_length=1, max_length=30)
    value: str = Field(min_length=1, max_length=60)
    tone: MetricTone = "NEUTRAL"


class MaterialParseRequest(BaseModel):
    merchant_id: str = Field(pattern=r"^[A-Za-z0-9_-]{2,40}$")
    group: MaterialGroup
    file_name: str = Field(min_length=3, max_length=160)
    media_type: str = Field(min_length=3, max_length=100)
    size_bytes: int = Field(gt=0, le=5 * 1024 * 1024)
    content_base64: str = Field(min_length=4)


class MaterialEvidence(BaseModel):
    material_id: str
    merchant_id: str
    group: MaterialGroup
    file_name: str
    media_type: str
    size_bytes: int
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    parse_status: Literal["PARSED"] = "PARSED"
    simulated: bool = True
    completeness_score: int = Field(ge=0, le=100)
    period_months: int | None = Field(default=None, ge=1, le=120)
    subject_match: bool
    extracted_metrics: list[ExtractedMetric]
    findings: list[str]
    warnings: list[str]

