from pathlib import Path
import csv
import sqlite3

DB_PATH = Path(r"E:\Codex\icbc_structured_tax_rules.db")
OUT_CSV = Path(r"E:\Codex\structured_scoring_results.csv")

def clamp(x, low=0, high=100):
    return max(low, min(high, x))

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = []
    for m in conn.execute("SELECT * FROM merchants ORDER BY merchant_id"):
        merchant_id = m["merchant_id"]
        facts = {r["field_name"]: r for r in conn.execute("SELECT * FROM merchant_basic_facts WHERE merchant_id=?", (merchant_id,))}
        monthly = conn.execute("SELECT * FROM merchant_monthly_series WHERE merchant_id=? ORDER BY month", (merchant_id,)).fetchall()
        fin = conn.execute("SELECT * FROM merchant_financial_snapshots WHERE merchant_id=?", (merchant_id,)).fetchone()
        inv = conn.execute("SELECT * FROM merchant_invoice_validations WHERE merchant_id=?", (merchant_id,)).fetchone()
        tax = fin

        receipts = [r["monthly_receipts"] or 0 for r in monthly]
        orders = [r["platform_orders"] or 0 for r in monthly]
        refunds = [r["platform_refund_rate"] for r in monthly if r["platform_refund_rate"] is not None]
        opened_months = facts.get("开业月数")["value_number"] if facts.get("开业月数") else 0
        staff = facts.get("员工/技师数量")["value_number"] if facts.get("员工/技师数量") else 1

        revenue_6m = sum(receipts[-6:])
        revenue_12m = sum(receipts)
        avg_6m = revenue_6m / 6 if revenue_6m else 0
        growth_6m = (receipts[-1] - receipts[-6]) / receipts[-6] if len(receipts) >= 6 and receipts[-6] else 0
        refund_6m = sum(refunds[-6:]) / min(6, len(refunds)) if refunds else 0
        cashflow_rate = None
        if fin and fin["operating_cash_inflow_6m"]:
            cashflow_rate = (fin["operating_cash_inflow_6m"] - (fin["operating_cash_outflow_6m"] or 0)) / fin["operating_cash_inflow_6m"]

        stability = 0
        stability += 30 if opened_months >= 36 else 22 if opened_months >= 12 else 12
        stability += 25 if cashflow_rate is not None and cashflow_rate >= 0.2 else 12 if cashflow_rate is not None and cashflow_rate >= 0 else 3
        stability += 20 if refund_6m <= 0.05 else 10 if refund_6m <= 0.1 else 2
        stability += 25 if revenue_6m > 300000 else 18 if revenue_6m > 150000 else 10

        growth = 50 + growth_6m * 220
        if avg_6m > 80000:
            growth += 10
        elif avg_6m < 40000:
            growth -= 8
        growth = clamp(growth)

        authenticity = 100
        if inv:
            if (inv["cashflow_abnormal_pattern_hits"] or 0) > 0:
                authenticity -= 25
            if inv["contract_invoice_match_result"] != "通过":
                authenticity -= 20
            if inv["sales_invoice_amount_12m"] and revenue_12m:
                gap = abs(inv["sales_invoice_amount_12m"] - revenue_12m) / revenue_12m
                if gap > 0.25:
                    authenticity -= 20
                elif gap > 0.15:
                    authenticity -= 10
        if not tax["tax_compliance_bool"]:
            authenticity -= 18
        if facts.get("法人个人授信情况") and facts["法人个人授信情况"]["value_text"] == "异常":
            authenticity -= 20
        authenticity = clamp(authenticity)

        utilization = (sum(orders[-6:]) / 6) / max(staff * 65, 1)
        capacity = clamp(90 - abs(utilization - 0.8) * 85)

        composite = round(stability * 0.35 + growth * 0.2 + authenticity * 0.3 + capacity * 0.15, 1)
        limit = round(max(avg_6m * (4.5 if composite >= 85 else 3.5 if composite >= 75 else 2.5 if composite >= 65 else 1.5 if composite >= 50 else 0), 0), 0)

        reasons = []
        if not tax["tax_compliance_bool"]:
            reasons.append("T01 纳税合规布尔值=FALSE")
        if inv and (inv["cashflow_abnormal_pattern_hits"] or 0) > 0:
            reasons.append("V04 流水异常模式命中")
        if inv and inv["contract_invoice_match_result"] != "通过":
            reasons.append("V05 合同发票匹配失败/待补充")
        if facts.get("法人个人授信情况") and facts["法人个人授信情况"]["value_text"] in ["异常", "未知"]:
            reasons.append("V07 法人授信状态异常或未知")

        row = {
            "merchant_id": merchant_id,
            "merchant_name": m["merchant_name"],
            "stability_score": round(stability, 1),
            "growth_score": round(growth, 1),
            "authenticity_score": round(authenticity, 1),
            "capacity_score": round(capacity, 1),
            "structured_composite_score": composite,
            "suggested_limit": limit,
            "manual_review_required": int(bool(reasons)),
            "manual_review_reasons": "；".join(reasons) if reasons else "未触发",
        }
        rows.append(row)
        conn.execute("INSERT OR REPLACE INTO structured_scoring_results VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
            merchant_id, row["merchant_name"], row["stability_score"], row["growth_score"], row["authenticity_score"], row["capacity_score"], row["structured_composite_score"], row["suggested_limit"], row["manual_review_required"], row["manual_review_reasons"]
        ))
    conn.commit()

    with OUT_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {OUT_CSV}")
    for row in rows:
        print(row)
    conn.close()

if __name__ == "__main__":
    main()
