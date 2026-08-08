from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from app.schemas.merchant import MerchantAnalysisRequest
from app.services.analysis_service import analyze_merchant

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "merchants.json"
FIXTURES = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda item: item["input"]["merchant_id"])
def test_legacy_profile_matches_excel_acceptance_table(fixture: dict) -> None:
    request = MerchantAnalysisRequest.model_validate(fixture["input"])
    result = analyze_merchant(request)
    expected = fixture["expected_legacy"]

    for field in (
        "stability",
        "growth",
        "authenticity",
        "capacity",
        "online_reputation",
        "social_activity",
        "complaint_risk",
        "unstructured",
    ):
        assert getattr(result.dimensions, field) == pytest.approx(expected[field], abs=0.05)

    assert result.operating_credit_score == pytest.approx(
        expected["operating_credit_score"], abs=0.05
    )
    assert result.limit.recommended_limit == expected["recommended_limit"]
    assert (
        result.features.final_inconsistency_count
        == expected["final_inconsistency_count"]
    )
    assert result.confidence == expected["confidence"]
    assert [hit.code for hit in result.review_rules] == expected["review_codes"]
    assert result.pd_12m is None
    assert result.pd_status == "UNCALIBRATED"


def test_feature_engine_reproduces_representative_excel_values() -> None:
    merchant_1 = analyze_merchant(
        MerchantAnalysisRequest.model_validate(FIXTURES[0]["input"])
    )
    assert merchant_1.features.receipts_6m == 532800
    assert merchant_1.features.receipts_12m == 1018000
    assert merchant_1.features.average_receipt_6m == 88800
    assert merchant_1.features.receipt_mom_growth == pytest.approx(0.0132, abs=0.00005)
    assert merchant_1.features.receipt_cagr_6m == pytest.approx(0.0148, abs=0.00005)
    assert merchant_1.features.order_receipt_correlation == pytest.approx(0.996, abs=0.0005)

    merchant_5 = analyze_merchant(
        MerchantAnalysisRequest.model_validate(FIXTURES[4]["input"])
    )
    assert merchant_5.features.structured_inconsistency_count == 2
    assert merchant_5.features.final_inconsistency_count == 3
    assert merchant_5.features.review_order_ratio is not None
    assert merchant_5.features.review_order_ratio > 0.50


def test_v5_profile_applies_new_reputation_weights_and_v09() -> None:
    raw = copy.deepcopy(FIXTURES[4]["input"])
    raw["profile"] = "v5_current"
    result = analyze_merchant(MerchantAnalysisRequest.model_validate(raw))

    assert result.dimensions.online_reputation == pytest.approx(59.0)
    assert result.dimensions.authenticity == pytest.approx(20.0)
    assert result.dimensions.unstructured == pytest.approx(65.8)
    assert result.operating_credit_score == pytest.approx(61.1)
    assert result.confidence == "LOW"
    assert [hit.code for hit in result.review_rules] == [
        "V01",
        "V04",
        "V05",
        "V06",
        "V07",
        "V09",
        "L01",
    ]


def test_v5_low_confidence_missing_merchant_triggers_l01_and_l02() -> None:
    raw = copy.deepcopy(FIXTURES[3]["input"])
    raw["profile"] = "v5_current"
    result = analyze_merchant(MerchantAnalysisRequest.model_validate(raw))

    assert result.confidence == "LOW"
    assert [hit.code for hit in result.review_rules] == ["L01", "L02"]
    assert result.decision == "MANUAL_REVIEW"

