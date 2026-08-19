from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.merchant import MerchantAnalysisRequest

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "merchants.json"
BASE_REQUEST = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))[0]["input"]


def test_monthly_series_must_have_same_length() -> None:
    raw = copy.deepcopy(BASE_REQUEST)
    raw["structural"]["monthly_orders"] = raw["structural"]["monthly_orders"][:-1]
    with pytest.raises(ValidationError, match="四组月度序列长度必须一致"):
        MerchantAnalysisRequest.model_validate(raw)


def test_monthly_series_requires_at_least_six_periods() -> None:
    raw = copy.deepcopy(BASE_REQUEST)
    for field in (
        "monthly_receipts",
        "monthly_orders",
        "monthly_redemption_rates",
        "monthly_refund_rates",
    ):
        raw["structural"][field] = raw["structural"][field][:5]
    with pytest.raises(ValidationError, match="月度序列至少需要6期"):
        MerchantAnalysisRequest.model_validate(raw)

