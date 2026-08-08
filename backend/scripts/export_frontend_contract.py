"""导出前端联调所需的 OpenAPI 与固定请求/响应样例。"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
OUTPUT_DIR = REPO_ROOT / "docs" / "api_examples"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app  # noqa: E402
from app.schemas.full_analysis import FullAnalysisRequest  # noqa: E402
from app.services.full_analysis_service import run_full_analysis  # noqa: E402


FIXED_GENERATED_AT = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(filename: str, payload: Any) -> None:
    (OUTPUT_DIR / filename).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _full_payload(index: int) -> dict[str, Any]:
    merchants = _load_json(BACKEND_ROOT / "tests" / "fixtures" / "merchants.json")
    transactions = _load_json(
        REPO_ROOT / "data" / "ml_simulated" / "transactions.json"
    )
    cashflows = _load_json(
        REPO_ROOT / "data" / "ml_simulated" / "cashflow_monthly.json"
    )
    return {
        "merchant": {**merchants[index]["input"], "profile": "v5_current"},
        "anomaly": transactions[index]["input"],
        "cash_gap": cashflows[index]["input"],
    }


def _response(payload: dict[str, Any]) -> dict[str, Any]:
    result = run_full_analysis(FullAnalysisRequest.model_validate(payload))
    result.generated_at = FIXED_GENERATED_AT
    return result.model_dump(mode="json")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    normal_request = _full_payload(0)
    review_request = _full_payload(4)
    _write_json("full_analysis_normal_request.json", normal_request)
    _write_json("full_analysis_normal_response.json", _response(normal_request))
    _write_json("full_analysis_review_request.json", review_request)
    _write_json("full_analysis_review_response.json", _response(review_request))
    _write_json("openapi.json", app.openapi())
    print(f"exported frontend API contract to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

