"""API 输入输出模型。"""
from app.schemas.anomaly import AnomalyAnalysisRequest, AnomalyAnalysisResult
from app.schemas.cash_gap import CashGapForecastRequest, CashGapForecastResult
from app.schemas.full_analysis import FullAnalysisRequest, FullAnalysisResult

__all__ = [
    "AnomalyAnalysisRequest",
    "AnomalyAnalysisResult",
    "CashGapForecastRequest",
    "CashGapForecastResult",
    "FullAnalysisRequest",
    "FullAnalysisResult",
]
