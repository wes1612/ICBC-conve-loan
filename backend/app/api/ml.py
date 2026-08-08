"""机器学习与统计模型服务接口。"""

from __future__ import annotations

from fastapi import APIRouter

from app.ml.anomaly_engine import analyze_transactions
from app.ml.cash_gap_engine import forecast_cash_gap
from app.schemas.analysis import AnalysisResult
from app.schemas.anomaly import AnomalyAnalysisRequest, AnomalyAnalysisResult
from app.schemas.cash_gap import CashGapForecastRequest, CashGapForecastResult
from app.schemas.full_analysis import FullAnalysisRequest, FullAnalysisResult
from app.schemas.merchant import MerchantAnalysisRequest
from app.services.analysis_service import analyze_merchant
from app.services.full_analysis_service import run_full_analysis


router = APIRouter(prefix="/api/v1/ml", tags=["machine-learning"])


@router.post("/score", response_model=AnalysisResult)
def score(request: MerchantAnalysisRequest) -> AnalysisResult:
    """返回经营信用评分、风险带、审核规则和建议额度。"""

    return analyze_merchant(request)


@router.post("/anomalies", response_model=AnomalyAnalysisResult)
def anomalies(request: AnomalyAnalysisRequest) -> AnomalyAnalysisResult:
    """识别近期交易异常并返回原因码与证据交易。"""

    return analyze_transactions(request)


@router.post("/cash-gap", response_model=CashGapForecastResult)
def cash_gap(request: CashGapForecastRequest) -> CashGapForecastResult:
    """预测未来三个月 P50/P90 经营资金缺口。"""

    return forecast_cash_gap(request)


@router.post("/full-analysis", response_model=FullAnalysisResult)
def full_analysis(request: FullAnalysisRequest) -> FullAnalysisResult:
    """一次返回评分、异常识别和资金缺口结果；后两项允许暂缺。"""

    return run_full_analysis(request)
