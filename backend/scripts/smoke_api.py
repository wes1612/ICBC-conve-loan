from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import httpx


BACKEND_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = BACKEND_ROOT / "tests" / "fixtures" / "merchants.json"
SIMULATED_DATA = BACKEND_ROOT.parent / "data" / "ml_simulated"
BASE_URL = "http://127.0.0.1:8765"


def application_context(merchant_id: str) -> dict:
    """Build the consent and data-scope context required by contract v0.4."""
    materials = [
        {
            "material_id": f"MAT-{merchant_id}-{group.upper()}-{index:08d}",
            "merchant_id": merchant_id,
            "group": group,
            "file_name": f"{merchant_id}_{group}.pdf",
            "media_type": "application/pdf",
            "size_bytes": 128,
            "sha256": f"{index:064x}",
            "parse_status": "PARSED",
            "simulated": True,
            "completeness_score": 95,
            "period_months": 12 if group in {"cashflow", "tax"} else None,
            "subject_match": True,
            "extracted_metrics": [{"label": "文件校验", "value": "已通过"}],
            "findings": ["冒烟测试材料已解析"],
            "warnings": [],
        }
        for index, group in enumerate(
            ["license", "cashflow", "statement", "tax", "plan"], start=1
        )
    ]
    return {
        "social_credit_code": f"91310000MA1DEMO{merchant_id[-3:]}",
        "operating_address": "上海市示范区惠民路 88 号",
        "legal_name": "李女士",
        "contact_phone": "13800000005",
        "identity_verified": True,
        "uploaded_data_groups": ["cashflow", "statement", "tax", "plan"],
        "authorized_sources": ["bank", "meituan", "enterprise"],
        "consent_confirmed": True,
        "consented_at": "2026-08-11T08:00:00Z",
        "materials": materials,
    }


def wait_until_ready(client: httpx.Client, process: subprocess.Popen[str]) -> None:
    for _ in range(50):
        if process.poll() is not None:
            break
        try:
            response = client.get("/health")
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            time.sleep(0.1)
    raise RuntimeError("API server did not become ready")


def main() -> None:
    merchants = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    merchant_5 = {**merchants[4]["input"], "profile": "v5_current"}
    transaction_cases = json.loads(
        (SIMULATED_DATA / "transactions.json").read_text(encoding="utf-8")
    )
    cashflow_cases = json.loads(
        (SIMULATED_DATA / "cashflow_monthly.json").read_text(encoding="utf-8")
    )
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8765",
        ],
        cwd=BACKEND_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )

    try:
        with httpx.Client(base_url=BASE_URL, timeout=5.0) as client:
            wait_until_ready(client, process)
            health = client.get("/health")
            result = client.post("/api/v1/ml/score", json=merchant_5)
            anomaly = client.post(
                "/api/v1/ml/anomalies", json=transaction_cases[4]["input"]
            )
            cash_gap = client.post(
                "/api/v1/ml/cash-gap", json=cashflow_cases[2]["input"]
            )
            full_analysis = client.post(
                "/api/v1/ml/full-analysis",
                json={
                    "application": application_context(merchant_5["merchant_id"]),
                    "merchant": merchant_5,
                    "anomaly": transaction_cases[4]["input"],
                    "cash_gap": cashflow_cases[4]["input"],
                },
            )
            cors = client.options(
                "/api/v1/ml/full-analysis",
                headers={
                    "Origin": "http://localhost:5173",
                    "Access-Control-Request-Method": "POST",
                },
            )
            docs = client.get("/docs")
            openapi = client.get("/openapi.json")

            health.raise_for_status()
            result.raise_for_status()
            anomaly.raise_for_status()
            cash_gap.raise_for_status()
            full_analysis.raise_for_status()
            cors.raise_for_status()
            docs.raise_for_status()
            openapi.raise_for_status()

            result_json = result.json()
            anomaly_json = anomaly.json()
            cash_gap_json = cash_gap.json()
            full_analysis_json = full_analysis.json()
            openapi_json = openapi.json()
            summary = {
                "health": health.json()["status"],
                "merchant_id": result_json["merchant_id"],
                "score": result_json["operating_credit_score"],
                "grade": result_json["credit_grade"],
                "recommended_limit": result_json["limit"]["recommended_limit"],
                "review_required": result_json["review_required"],
                "triggered_rules": [
                    rule["code"] for rule in result_json["review_rules"]
                ],
                "anomaly_score": anomaly_json["anomaly_score"],
                "anomaly_risk_level": anomaly_json["risk_level"],
                "anomaly_reason_codes": anomaly_json["reason_codes"],
                "cash_gap_merchant_id": cash_gap_json["merchant_id"],
                "cash_gap_risk_level": cash_gap_json["risk_level"],
                "max_p50_funding_gap": cash_gap_json["max_p50_funding_gap"],
                "max_p90_funding_gap": cash_gap_json["max_p90_funding_gap"],
                "full_analysis_overall_risk": full_analysis_json["overall_risk"],
                "full_analysis_overall_decision": full_analysis_json[
                    "overall_decision"
                ],
                "full_analysis_module_states": full_analysis_json["module_states"],
                "full_analysis_material_count": len(
                    full_analysis_json["material_evidence"]
                ),
                "cors_allow_origin": cors.headers.get("access-control-allow-origin"),
                "docs_status": docs.status_code,
                "ml_paths_in_openapi": all(
                    path in openapi_json["paths"]
                    for path in (
                        "/api/v1/ml/score",
                        "/api/v1/ml/anomalies",
                        "/api/v1/ml/cash-gap",
                        "/api/v1/ml/full-analysis",
                        "/api/v1/materials/parse",
                    )
                ),
            }
            print(json.dumps(summary, ensure_ascii=False, indent=2))
    except Exception:
        process.terminate()
        stdout, stderr = process.communicate(timeout=5)
        if stdout:
            print(stdout, file=sys.stderr)
        if stderr:
            print(stderr, file=sys.stderr)
        raise
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


if __name__ == "__main__":
    main()
