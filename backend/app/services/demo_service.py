"""Read the five simulated merchants and build runnable website demo cases."""

from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import secrets
from typing import Any

from app.schemas.demo import DemoApplicant, DemoCasePayload, DemoMerchantId
from app.schemas.full_analysis import ApplicationContext, FullAnalysisRequest
from app.schemas.material import MaterialEvidence, MaterialGroup
from app.schemas.merchant import MerchantAnalysisRequest
from app.schemas.anomaly import AnomalyAnalysisRequest
from app.schemas.cash_gap import CashGapForecastRequest
from app.services.full_analysis_service import run_full_analysis


REPO_ROOT = Path(__file__).resolve().parents[3]
SIMULATED_DB_ROOT = REPO_ROOT / "data" / "ml_simulated"
MERCHANT_FIXTURE = REPO_ROOT / "backend" / "tests" / "fixtures" / "merchants.json"
DEMO_IDS: tuple[DemoMerchantId, ...] = ("M001", "M002", "M003", "M004", "M005")

APPLICANT_DETAILS: dict[DemoMerchantId, dict[str, str]] = {
    "M001": {"legal": "李女士", "address": "示范区惠民路 88 号", "birth": "199001010011"},
    "M002": {"legal": "陈女士", "address": "示范区惠民路 108 号", "birth": "199202020022"},
    "M003": {"legal": "赵女士", "address": "示范区惠民路 128 号", "birth": "199303030033"},
    "M004": {"legal": "周先生", "address": "示范区惠民路 168 号", "birth": "198804040044"},
    "M005": {"legal": "王女士", "address": "示范区惠民路 188 号", "birth": "199205050055"},
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _database() -> dict[str, dict[str, Any]]:
    merchants = {
        item["input"]["merchant_id"]: item["input"]
        for item in _load_json(MERCHANT_FIXTURE)
    }
    anomalies = {
        item["input"]["merchant_id"]: item["input"]
        for item in _load_json(SIMULATED_DB_ROOT / "transactions.json")
    }
    cash_gaps = {
        item["input"]["merchant_id"]: item["input"]
        for item in _load_json(SIMULATED_DB_ROOT / "cashflow_monthly.json")
    }
    return {
        merchant_id: {
            "merchant": merchants[merchant_id],
            "anomaly": anomalies[merchant_id],
            "cash_gap": cash_gaps[merchant_id],
        }
        for merchant_id in DEMO_IDS
    }


def _money(value: float | int | None) -> str:
    return "未提供" if value is None else f"¥{value:,.0f}"


def _material(
    merchant: MerchantAnalysisRequest,
    cash_gap: CashGapForecastRequest,
    group: MaterialGroup,
) -> MaterialEvidence:
    merchant_id = merchant.merchant_id
    structural = merchant.structural
    digest = hashlib.sha256(f"simdb:{merchant_id}:{group}:v1".encode()).hexdigest()
    period = 12 if group in {"cashflow", "tax"} else 3 if group == "plan" else None
    completeness = 80
    subject_match = True
    metrics: list[dict[str, str]] = []
    findings: list[str] = []
    warnings: list[str] = []

    if group == "license":
        subject_match = structural.license_subject == structural.merchant_name
        completeness = 98 if subject_match else 76
        metrics = [
            {"label": "经营状态", "value": structural.legal_credit_status, "tone": "POSITIVE" if structural.legal_credit_status == "正常" else "WARNING"},
            {"label": "经营月数", "value": f"{structural.months_in_business} 个月", "tone": "NEUTRAL"},
        ]
        findings = ["模拟工商主体记录已载入", "主体名称与申请信息一致" if subject_match else "登记主体与申请主体存在差异"]
        if not subject_match:
            warnings.append("请人工核实营业执照主体差异")
    elif group == "cashflow":
        subject_match = structural.account_holder == structural.merchant_name
        completeness = 94 if subject_match else 78
        average_receipts = sum(structural.monthly_receipts) / len(structural.monthly_receipts)
        metrics = [
            {"label": "月均经营流入", "value": _money(average_receipts), "tone": "POSITIVE" if structural.transaction_anomaly_hits == 0 else "WARNING"},
            {"label": "异常命中", "value": f"{structural.transaction_anomaly_hits} 项", "tone": "POSITIVE" if structural.transaction_anomaly_hits == 0 else "DANGER"},
        ]
        findings = ["已载入连续经营流水", "收款账户主体一致" if subject_match else "收款账户主体与申请主体不一致"]
        if not subject_match:
            warnings.append("流水账户主体需要补充说明")
    elif group == "statement":
        has_statement = structural.total_assets is not None and structural.total_liabilities is not None
        subject_match = has_statement
        completeness = 92 if has_statement else 52
        debt_ratio = (
            structural.total_liabilities / structural.total_assets * 100
            if structural.total_assets and structural.total_liabilities is not None
            else None
        )
        metrics = [
            {"label": "资产总额", "value": _money(structural.total_assets), "tone": "NEUTRAL"},
            {"label": "资产负债率", "value": "未提供" if debt_ratio is None else f"{debt_ratio:.1f}%", "tone": "WARNING" if debt_ratio is not None and debt_ratio >= 65 else "NEUTRAL"},
        ]
        findings = ["最近一期资产负债摘要已载入" if has_statement else "资产负债关键字段缺失"]
        if not has_statement:
            warnings.append("需要补充完整资产负债资料")
    elif group == "tax":
        subject_match = structural.invoice_issuer == structural.merchant_name
        completeness = 91 if structural.sales_invoice_amount_12m is not None else 48
        receipt_total = sum(structural.monthly_receipts)
        coverage = (
            structural.sales_invoice_amount_12m / receipt_total * 100
            if structural.sales_invoice_amount_12m is not None and receipt_total
            else None
        )
        metrics = [
            {"label": "开票收入", "value": _money(structural.sales_invoice_amount_12m), "tone": "NEUTRAL"},
            {"label": "开票覆盖率", "value": "未提供" if coverage is None else f"{coverage:.1f}%", "tone": "WARNING" if coverage is None or coverage < 70 else "POSITIVE"},
        ]
        findings = ["模拟纳税与开票记录已载入" if coverage is not None else "纳税开票关键字段缺失"]
        if not subject_match or coverage is None:
            warnings.append("开票主体或资料完整性需要人工核实")
    elif group == "plan":
        has_plan = structural.plan_score is not None
        subject_match = has_plan
        completeness = max(45, round(structural.plan_score or 0))
        metrics = [
            {"label": "经营计划评分", "value": "未提供" if structural.plan_score is None else f"{structural.plan_score:g}", "tone": "WARNING" if structural.plan_score is None or structural.plan_score < 60 else "NEUTRAL"},
            {"label": "计划资本开支", "value": _money(sum(cash_gap.planned_capex_3m)), "tone": "NEUTRAL"},
        ]
        findings = ["未来三个月经营与资金计划已载入" if has_plan else "经营计划信息尚不完整"]
        if not has_plan:
            warnings.append("需要补充经营计划和资金用途")
    else:
        completeness = 72
        metrics = [{"label": "材料属性", "value": "可选补充", "tone": "NEUTRAL"}]
        findings = ["模拟经营资产记录已载入，不作为必备抵押物"]

    return MaterialEvidence(
        material_id=f"MAT-{merchant_id}-{group.upper()}-{digest[:8]}",
        merchant_id=merchant_id,
        group=group,
        file_name=f"{merchant_id}_{group}_simulated_record.json",
        media_type="application/json",
        size_bytes=2048 + len(group) * 97,
        sha256=digest,
        simulated=True,
        completeness_score=completeness,
        period_months=period,
        subject_match=subject_match,
        extracted_metrics=metrics,
        findings=findings,
        warnings=warnings,
    )


def _applicant(merchant: MerchantAnalysisRequest) -> DemoApplicant:
    merchant_id = merchant.merchant_id
    details = APPLICANT_DETAILS[merchant_id]  # type: ignore[index]
    ordinal = int(merchant_id[-1])
    id_number = f"310101{details['birth']}"
    phone = f"1380000000{ordinal}"
    return DemoApplicant(
        merchant_name=merchant.structural.merchant_name,
        industry=merchant.structural.industry,
        social_credit_code=f"91310000MA1DEMO{ordinal:03d}",
        province="上海市",
        city="上海市",
        address=details["address"],
        legal_name=details["legal"],
        legal_phone=phone,
        legal_id_number=id_number,
        contact_name=details["legal"],
        contact_phone=phone,
        contact_id_number=id_number,
        requested_amount=merchant.structural.requested_amount,
    )


@lru_cache(maxsize=5)
def get_demo_case(merchant_id: DemoMerchantId) -> DemoCasePayload:
    record = _database()[merchant_id]
    merchant = MerchantAnalysisRequest.model_validate(
        {**record["merchant"], "profile": "v5_current"}
    )
    anomaly = AnomalyAnalysisRequest.model_validate(record["anomaly"])
    cash_gap = CashGapForecastRequest.model_validate(record["cash_gap"])
    applicant = _applicant(merchant)
    materials = [
        _material(merchant, cash_gap, group)
        for group in ("license", "cashflow", "statement", "tax", "plan", "asset")
    ]
    application = ApplicationContext(
        social_credit_code=applicant.social_credit_code,
        province=applicant.province,
        city=applicant.city,
        operating_address=f"{applicant.province}{applicant.city}{applicant.address}",
        legal_name=applicant.legal_name,
        legal_phone=applicant.legal_phone,
        legal_id_number=applicant.legal_id_number,
        contact_name=applicant.contact_name,
        contact_phone=applicant.contact_phone,
        contact_id_number=applicant.contact_id_number,
        identity_verified=True,
        uploaded_data_groups=["cashflow", "statement", "tax", "plan"],
        authorized_sources=["bank", "meituan", "enterprise"],
        consent_confirmed=True,
        consented_at=datetime(2026, 8, 17, tzinfo=timezone.utc),
        materials=materials,
    )
    preview = run_full_analysis(
        FullAnalysisRequest(
            application=application,
            merchant=merchant,
            anomaly=anomaly,
            cash_gap=cash_gap,
        )
    )
    labels = {
        "APPROVE": ("审批建议案例", "规则结果为审批建议，仍不代表真实银行承诺。"),
        "MANUAL_REVIEW": ("人工复核案例", "命中审核门控，需要结合证据进行人工核查。"),
        "DECLINE": ("审慎拒绝案例", "当前结构化结果不支持自动授信，需核实数据与风险。"),
    }
    label, description = labels[preview.overall_decision]
    return DemoCasePayload(
        merchant_id=merchant_id,
        case_label=label,
        case_description=description,
        expected_risk=preview.overall_risk,
        expected_decision=preview.overall_decision,
        applicant=applicant,
        merchant=merchant,
        anomaly=anomaly,
        cash_gap=cash_gap,
        materials=materials,
    )


def random_demo_case(exclude: DemoMerchantId | None = None) -> DemoCasePayload:
    candidates = [merchant_id for merchant_id in DEMO_IDS if merchant_id != exclude]
    return get_demo_case(secrets.choice(candidates))

