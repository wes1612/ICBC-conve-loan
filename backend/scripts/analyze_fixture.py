"""无需启动 HTTP 服务即可运行测试商户。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.schemas.merchant import MerchantAnalysisRequest
from app.services.analysis_service import analyze_merchant

FIXTURE_PATH = BACKEND_DIR / "tests" / "fixtures" / "merchants.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("merchant_id", nargs="?", default="M001")
    parser.add_argument(
        "--profile",
        choices=["v5_current", "legacy_acceptance"],
        default="v5_current",
    )
    args = parser.parse_args()

    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    raw = next(item["input"] for item in fixtures if item["input"]["merchant_id"] == args.merchant_id)
    raw["profile"] = args.profile
    result = analyze_merchant(MerchantAnalysisRequest.model_validate(raw))
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
