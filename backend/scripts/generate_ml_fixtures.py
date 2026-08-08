"""生成可复现的五商户交易明细与月度现金流模拟数据。"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
MERCHANT_FIXTURE = BACKEND_ROOT / "tests" / "fixtures" / "merchants.json"
OUTPUT_DIR = REPO_ROOT / "data" / "ml_simulated"
SNAPSHOT_DATE = date(2026, 7, 31)

TRANSACTION_WEIGHTS = (0.10, 0.11, 0.12, 0.13, 0.14, 0.13, 0.14, 0.13)
SPARSE_TRANSACTION_WEIGHTS = (0.30, 0.33, 0.37)

CASH_SETTINGS: dict[str, dict[str, Any]] = {
    "M001": {
        "current_cash_balance": 160_000,
        "restricted_cash": 5_000,
        "unused_credit": 80_000,
        "minimum_cash_balance": 50_000,
        "planned_capex_3m": [0, 10_000, 0],
        "debt_service_3m": [8_000, 8_000, 8_000],
        "confirmed_extra_inflows_3m": [0, 0, 0],
    },
    "M002": {
        "current_cash_balance": 55_000,
        "restricted_cash": 0,
        "unused_credit": 100_000,
        "minimum_cash_balance": 45_000,
        "planned_capex_3m": [80_000, 120_000, 0],
        "debt_service_3m": [5_000, 5_000, 5_000],
        "confirmed_extra_inflows_3m": [30_000, 0, 0],
    },
    "M003": {
        "current_cash_balance": 12_000,
        "restricted_cash": 2_000,
        "unused_credit": 20_000,
        "minimum_cash_balance": 35_000,
        "planned_capex_3m": [0, 0, 0],
        "debt_service_3m": [8_000, 8_000, 8_000],
        "confirmed_extra_inflows_3m": [0, 0, 0],
    },
    "M004": {
        "current_cash_balance": 25_000,
        "restricted_cash": 5_000,
        "unused_credit": 30_000,
        "minimum_cash_balance": 40_000,
        "planned_capex_3m": [20_000, 0, 0],
        "debt_service_3m": [4_000, 4_000, 4_000],
        "confirmed_extra_inflows_3m": [0, 0, 0],
    },
    "M005": {
        "current_cash_balance": 75_000,
        "restricted_cash": 10_000,
        "unused_credit": 50_000,
        "minimum_cash_balance": 45_000,
        "planned_capex_3m": [40_000, 20_000, 0],
        "debt_service_3m": [6_000, 6_000, 6_000],
        "confirmed_extra_inflows_3m": [0, 0, 0],
    },
}


def _month_starts() -> list[date]:
    values: list[date] = []
    for index in range(12):
        month_index = 2025 * 12 + 7 + index
        values.append(date(month_index // 12, month_index % 12 + 1, 1))
    return values


def _transaction(
    merchant_id: str,
    transaction_id: str,
    transaction_time: datetime,
    direction: str,
    amount: float,
    counterparty: str,
    channel: str,
    *,
    order_id: str | None = None,
    invoice_id: str | None = None,
    business_hour: bool = True,
) -> dict[str, Any]:
    return {
        "merchant_id": merchant_id,
        "transaction_id": transaction_id,
        "transaction_time": transaction_time.isoformat(),
        "direction": direction,
        "amount": round(amount, 2),
        "counterparty_hash": counterparty,
        "channel": channel,
        "status": "SUCCESS",
        "order_id_hash": order_id,
        "invoice_id_hash": invoice_id,
        "purpose_code": "OPERATING",
        "is_business_hour": business_hour,
    }


def _build_transactions(merchant: dict[str, Any]) -> dict[str, Any]:
    request = merchant["input"]
    merchant_id = request["merchant_id"]
    receipts = request["structural"]["monthly_receipts"]
    transactions: list[dict[str, Any]] = []
    sequence = 1

    for month_index, (month, receipt) in enumerate(zip(_month_starts(), receipts, strict=True)):
        weights = (
            SPARSE_TRANSACTION_WEIGHTS if merchant_id == "M004" else TRANSACTION_WEIGHTS
        )
        for item_index, weight in enumerate(weights):
            transaction_id = f"{merchant_id}-T{sequence:04d}"
            clustered = merchant_id == "M005" and month_index == 11
            counterparty = (
                "CP-M005-CLUSTER"
                if clustered
                else f"CP-{merchant_id}-{month_index:02d}-{item_index:02d}"
            )
            transactions.append(
                _transaction(
                    merchant_id,
                    transaction_id,
                    datetime(month.year, month.month, 3 + item_index * 3, 10 + item_index % 7, 15),
                    "IN",
                    receipt * weight,
                    counterparty,
                    "COLLECTION",
                    order_id=f"ORDER-{merchant_id}-{month_index:02d}-{item_index:02d}",
                    invoice_id=f"INV-{merchant_id}-{month_index:02d}-{item_index:02d}",
                )
            )
            sequence += 1

        for item_index, share in enumerate((0.18, 0.12)):
            transaction_id = f"{merchant_id}-T{sequence:04d}"
            transactions.append(
                _transaction(
                    merchant_id,
                    transaction_id,
                    datetime(month.year, month.month, 12 + item_index * 10, 14, 0),
                    "OUT",
                    receipt * share,
                    f"SUPPLIER-{merchant_id}-{item_index}",
                    "TRANSFER",
                )
            )
            sequence += 1

    if merchant_id == "M003":
        for day in (18, 22, 26):
            transactions.append(
                _transaction(
                    merchant_id,
                    f"{merchant_id}-T{sequence:04d}",
                    datetime(2026, 7, day, 16, 0),
                    "OUT",
                    1200,
                    f"CUSTOMER-REFUND-{day}",
                    "REFUND",
                )
            )
            sequence += 1

    if merchant_id == "M005":
        for minute in (5, 15, 25, 35, 45):
            transactions.append(
                _transaction(
                    merchant_id,
                    f"{merchant_id}-T{sequence:04d}",
                    datetime(2026, 7, 18, 1, minute),
                    "IN",
                    5000,
                    "CP-M005-CLUSTER",
                    "COLLECTION",
                    business_hour=False,
                )
            )
            sequence += 1
        transactions.append(
            _transaction(
                merchant_id,
                f"{merchant_id}-T{sequence:04d}",
                datetime(2026, 7, 18, 2, 5),
                "OUT",
                4950,
                "CP-M005-CLUSTER",
                "TRANSFER",
                business_hour=False,
            )
        )
        sequence += 1
        for day in (21, 23, 25, 27):
            transactions.append(
                _transaction(
                    merchant_id,
                    f"{merchant_id}-T{sequence:04d}",
                    datetime(2026, 7, day, 15, 30),
                    "OUT",
                    1800,
                    f"CUSTOMER-REFUND-{day}",
                    "REFUND",
                )
            )
            sequence += 1

    return {
        "case_id": f"{merchant_id}_transaction_case",
        "source_type": "SIMULATED_FOR_COMPETITION_MVP",
        "injected_anomalies": (
            [
                "REPEATED_ROUND_AMOUNT",
                "OFF_HOURS_CONCENTRATION",
                "COUNTERPARTY_CONCENTRATION",
                "RAPID_IN_OUT_ROUNDTRIP",
                "HIGH_REFUND_REVERSAL",
                "MISSING_ORDER_LINK",
            ]
            if merchant_id == "M005"
            else ["HIGH_REFUND_REVERSAL"] if merchant_id == "M003" else []
        ),
        "input": {
            "merchant_id": merchant_id,
            "as_of_time": "2026-07-31T23:59:59",
            "transactions": transactions,
        },
    }


def _build_cashflow(merchant: dict[str, Any]) -> dict[str, Any]:
    request = merchant["input"]
    merchant_id = request["merchant_id"]
    structural = request["structural"]
    receipts = [float(value) for value in structural["monthly_receipts"]]
    six_month_receipts = sum(receipts[-6:])
    inflow_total = structural["operating_cash_inflow_6m"]
    inflow_scale = inflow_total / six_month_receipts if inflow_total else 0.95
    inflows = [value * inflow_scale for value in receipts]

    outflow_total = structural["operating_cash_outflow_6m"]
    outflow_ratio = outflow_total / sum(inflows[-6:]) if outflow_total else 0.82
    raw_outflows = [
        inflow * outflow_ratio * factor
        for inflow, factor in zip(
            inflows,
            (1.02, 0.99, 1.01, 1.00, 1.03, 0.98, 1.02, 1.00, 0.99, 1.01, 1.03, 0.97),
            strict=True,
        )
    ]
    if outflow_total:
        normalization = outflow_total / sum(raw_outflows[-6:])
        outflows = [value * normalization for value in raw_outflows]
    else:
        outflows = raw_outflows

    history = [
        {
            "month": month.isoformat(),
            "operating_inflow": round(inflow, 2),
            "operating_outflow": round(outflow, 2),
        }
        for month, inflow, outflow in zip(
            _month_starts(), inflows, outflows, strict=True
        )
    ]
    return {
        "case_id": f"{merchant_id}_cash_gap_case",
        "source_type": "SIMULATED_FOR_COMPETITION_MVP",
        "input": {
            "merchant_id": merchant_id,
            "snapshot_date": SNAPSHOT_DATE.isoformat(),
            "history": history,
            **CASH_SETTINGS[merchant_id],
            "stress_inflow_decline": 0.15,
            "stress_outflow_increase": 0.10,
        },
    }


def main() -> None:
    merchants = json.loads(MERCHANT_FIXTURE.read_text(encoding="utf-8"))
    transaction_cases = [_build_transactions(merchant) for merchant in merchants]
    cashflow_cases = [_build_cashflow(merchant) for merchant in merchants]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "transactions.json").write_text(
        json.dumps(transaction_cases, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OUTPUT_DIR / "cashflow_monthly.json").write_text(
        json.dumps(cashflow_cases, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"generated {sum(len(case['input']['transactions']) for case in transaction_cases)} "
        f"transactions and {sum(len(case['input']['history']) for case in cashflow_cases)} "
        f"cashflow months in {OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()

