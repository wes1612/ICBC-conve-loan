"""统一商户分析服务。"""

from __future__ import annotations

from app.ml.config import PROFILE_CONFIGS
from app.ml.decision_engine import (
    calculate_limit,
    confidence_level,
    credit_grade,
    decision_and_risk,
    evaluate_review_rules,
    explain_dimensions,
)
from app.ml.feature_engine import build_features
from app.ml.scorecard import calculate_composite, calculate_dimensions
from app.schemas.analysis import AnalysisResult
from app.schemas.merchant import MerchantAnalysisRequest


def analyze_merchant(request: MerchantAnalysisRequest) -> AnalysisResult:
    features = build_features(request)
    dimensions = calculate_dimensions(request, features)
    composite = calculate_composite(request, features, dimensions)
    confidence = confidence_level(request, features)
    review_rules = evaluate_review_rules(request, features, confidence)
    decision, risk_band = decision_and_risk(composite, review_rules)
    limit = calculate_limit(request, features, dimensions, composite)
    positive, negative = explain_dimensions(dimensions)

    return AnalysisResult(
        merchant_id=request.merchant_id,
        merchant_name=request.structural.merchant_name,
        profile=request.profile,
        score_version=str(PROFILE_CONFIGS[request.profile]["score_version"]),
        features=features,
        dimensions=dimensions,
        operating_credit_score=composite,
        credit_grade=credit_grade(composite),  # type: ignore[arg-type]
        risk_band=risk_band,  # type: ignore[arg-type]
        confidence=confidence,  # type: ignore[arg-type]
        decision=decision,  # type: ignore[arg-type]
        review_required=bool(review_rules),
        review_rules=review_rules,
        positive_reasons=positive,
        negative_reasons=negative,
        limit=limit,
    )

