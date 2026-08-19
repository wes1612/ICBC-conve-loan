"""Lightweight loan product layer for presenting credit terms.

This module wraps existing deterministic score/anomaly/cash-gap outputs into
bank-product concepts. It does not change the v5 scorecard formula.
"""

from __future__ import annotations

from datetime import datetime
from statistics import mean
from typing import Literal

from app.schemas.analysis import AnalysisResult
from app.schemas.cash_gap import CashGapForecastResult
from app.schemas.full_analysis import (
    ApplicationContext,
    AuditTrail,
    EligibilityResult,
    LoanTerms,
    RepaymentCapacity,
)


PILOT_INDUSTRIES = {"美容美发", "宠物服务", "生活服务"}


def _round_down_thousand(value: float) -> int:
    return max(0, int(value // 1000) * 1000)


def _use_case_policy(use_of_funds: str) -> tuple[str, list[str]]:
    policies = {
        "设备采购": ("匹配", ["核查设备采购合同或报价单", "关注设备投入后服务承接能力提升"]),
        "装修扩店": ("审慎匹配", ["需核查租赁期限与装修预算", "关注扩店期现金流压力"]),
        "旺季备货": ("匹配", ["核查历史旺季订单和核销记录", "适合短周期循环额度"]),
        "人员扩充": ("匹配", ["关注工资刚性支出增加", "建议结合订单增长分阶段提款"]),
        "平台活动垫资": ("审慎匹配", ["关注平台回款周期", "退款率升高时限制提款"]),
        "租金工资周转": ("审慎匹配", ["关注固定支出覆盖率", "不宜超过短期现金流承受能力"]),
    }
    return policies.get(
        use_of_funds,
        ("需补充说明", ["资金用途不在首期规则表内", "建议补充合同、报价单或经营计划说明"]),
    )


def build_eligibility(application: ApplicationContext, score: AnalysisResult) -> EligibilityResult:
    warnings: list[str] = []
    industry = application.industry or "未填写"
    if industry not in PILOT_INDUSTRIES:
        warnings.append(f"{industry} 不在首期试点行业内")
    if score.review_required:
        warnings.append("命中评分人工审核规则")
    if score.confidence == "LOW":
        warnings.append("数据置信度低")

    if industry not in PILOT_INDUSTRIES:
        status: Literal["ELIGIBLE", "SUPPLEMENT_REQUIRED", "OUT_OF_SCOPE", "MANUAL_REVIEW"] = "OUT_OF_SCOPE"
        conclusion = "不在首期试点范围"
    elif score.review_required:
        status = "MANUAL_REVIEW"
        conclusion = "符合客群但需人工审核"
    elif score.confidence == "LOW":
        status = "SUPPLEMENT_REQUIRED"
        conclusion = "需补充材料后再测算"
    else:
        status = "ELIGIBLE"
        conclusion = "符合试点客群"

    return EligibilityResult(
        status=status,
        conclusion=conclusion,
        pilot_industry=industry in PILOT_INDUSTRIES,
        reasons=[
            f"所属行业：{industry}",
            f"经营信用等级：{score.credit_grade}",
            f"数据置信度：{score.confidence}",
        ],
        warnings=warnings,
    )


def build_loan_terms(
    application: ApplicationContext,
    score: AnalysisResult,
    overall_decision: str,
    cash_gap: CashGapForecastResult | None,
) -> LoanTerms:
    requested = application.requested_amount
    base_limit = _round_down_thousand(score.limit.recommended_limit)
    max_p90_gap = cash_gap.max_p90_funding_gap if cash_gap else 0
    use_match, use_warnings = _use_case_policy(application.use_of_funds)

    if overall_decision == "DECLINE":
        final_limit = 0
        tenor = 0
        repayment = "暂不配置还款方式"
        revolving = False
        drawdown = "暂不开放提款"
    elif overall_decision == "MANUAL_REVIEW":
        final_limit = _round_down_thousand(min(base_limit, requested, 200_000))
        tenor = min(application.requested_tenor_months, 6)
        repayment = "人工复核后确定"
        revolving = False
        drawdown = "完成补件和用途核验后，由客户经理人工放行"
    else:
        stress_adjusted = base_limit * (0.8 if max_p90_gap > base_limit * 0.35 else 1.0)
        final_limit = _round_down_thousand(min(stress_adjusted, requested * 1.1))
        tenor_cap = 12 if score.risk_band == "LOW" and max_p90_gap <= base_limit * 0.35 else 6
        tenor = min(application.requested_tenor_months, tenor_cap)
        repayment = "按月付息，到期还本；支持随借随还"
        revolving = tenor >= 12
        drawdown = "单笔提款不超过建议额度的30%，资金用途需匹配本次经营计划"

    lower = _round_down_thousand(final_limit * 0.8)
    upper = _round_down_thousand(final_limit)
    if final_limit == 0:
        lower = 0

    use_warnings = [*use_warnings]
    if requested > base_limit * 1.3:
        use_warnings.append("申请金额明显高于模型建议额度，需解释资金用途和还款来源")
    if max_p90_gap > 0:
        use_warnings.append(f"P90压力情景最大资金缺口约 {max_p90_gap:,.0f} 元")

    return LoanTerms(
        requested_amount=requested,
        recommended_limit=final_limit,
        limit_range=[lower, upper],
        tenor_months=tenor,
        repayment_method=repayment,
        is_revolving=revolving,
        drawdown_rule=drawdown,
        renewal_rule="连续三个月无逾期且订单、流水、退款投诉未恶化，可进入续贷或提额评估",
        limit_adjustment_rule="触发异常交易、授权中断、P90资金缺口恶化或重大投诉时，进入降额、冻结或人工复核",
        use_of_funds=application.use_of_funds,
        use_of_funds_match=use_match,
        use_of_funds_warnings=use_warnings,
        expected_repayment_source=application.expected_repayment_source,
        repayment_source_note="还款来源由申请人填写，并结合现金流、订单和授权流水交叉验证。",
    )


def build_repayment_capacity(score: AnalysisResult, cash_gap: CashGapForecastResult | None) -> RepaymentCapacity:
    if cash_gap and cash_gap.forecasts:
        avg_inflow = mean(item.p50_operating_inflow for item in cash_gap.forecasts)
        avg_outflow = mean(item.p50_operating_outflow for item in cash_gap.forecasts)
        fixed_coverage = round(avg_inflow / avg_outflow, 2) if avg_outflow else None
        p90_gap = cash_gap.max_p90_funding_gap
        cash_pressure = cash_gap.risk_level
    else:
        avg_inflow = None
        avg_outflow = None
        fixed_coverage = None
        p90_gap = None
        cash_pressure = "NOT_PROVIDED"

    if score.review_required or cash_pressure == "HIGH":
        conclusion = "偿债能力需人工复核"
        confidence = "MEDIUM" if score.confidence != "LOW" else "LOW"
    elif score.risk_band == "LOW" and cash_pressure in {"LOW", "MEDIUM"}:
        conclusion = "经营现金流对拟授信具备基础覆盖能力"
        confidence = score.confidence
    else:
        conclusion = "偿债能力存在关注项"
        confidence = "MEDIUM"

    evidence = [
        f"经营信用分 {score.operating_credit_score:.1f}，等级 {score.credit_grade}",
        f"评分风险带 {score.risk_band}，数据置信度 {score.confidence}",
    ]
    if p90_gap is not None:
        evidence.append(f"未来三个月 P90 最大资金缺口约 {p90_gap:,.0f} 元")

    return RepaymentCapacity(
        conclusion=conclusion,
        confidence=confidence,
        monthly_operating_inflow=avg_inflow,
        monthly_operating_outflow=avg_outflow,
        fixed_cost_coverage=fixed_coverage,
        p90_funding_gap=p90_gap,
        debt_pressure_level=cash_pressure,
        refund_complaint_pressure="由退款率、投诉风险和异常交易规则共同观察",
        evidence=evidence,
    )


def build_audit_trail(
    application: ApplicationContext,
    generated_at: datetime,
    score: AnalysisResult,
    ai_used: bool = False,
) -> AuditTrail:
    return AuditTrail(
        consent_version=application.consent_version,
        consent_timestamp=application.consented_at,
        authorized_sources=application.authorized_sources,
        material_hashes={material.material_id: material.sha256 for material in application.materials},
        material_ids=[material.material_id for material in application.materials],
        score_version=score.score_version,
        rules_version=score.profile,
        model_version="scorecard_v5 + anomaly_hybrid_v1 + cash_gap_baseline_v1",
        generated_at=generated_at,
        ai_used=ai_used,
    )
