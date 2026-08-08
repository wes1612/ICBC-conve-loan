"""商户评分 API。"""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.analysis import AnalysisResult
from app.schemas.merchant import MerchantAnalysisRequest
from app.services.analysis_service import analyze_merchant

router = APIRouter(prefix="/api/v1", tags=["analysis"])


@router.post("/analyze", response_model=AnalysisResult)
def analyze(request: MerchantAnalysisRequest) -> AnalysisResult:
    """使用指定规则版本分析一个商户。"""

    return analyze_merchant(request)

