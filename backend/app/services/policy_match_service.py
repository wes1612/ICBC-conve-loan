"""Policy and ICBC consumption-introduction matching service.

The database is intentionally file-backed for the MVP. Search or AI discovery
should only create candidates; ACTIVE recommendations must keep source links
and review traces before they are shown as applicable policies.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from app.schemas.analysis import AnalysisResult
from app.schemas.full_analysis import ApplicationContext, PolicyRecommendation


REPO_ROOT = Path(__file__).resolve().parents[3]
POLICY_DIR = REPO_ROOT / "data" / "policies"
MAX_RECOMMENDATIONS = 4


def _load_json(filename: str) -> dict[str, Any]:
    return json.loads((POLICY_DIR / filename).read_text(encoding="utf-8"))


def _normal_industry(value: str | None) -> str:
    if not value:
        return "生活服务"
    if value in {"美容美发", "宠物服务", "生活服务", "艺术教育", "餐饮住宿", "休闲娱乐"}:
        return value
    return "生活服务"


def _is_current(policy: dict[str, Any], today: date) -> bool:
    if policy.get("status") not in {"ACTIVE", "DRAFT"}:
        return False
    expiry = policy.get("expiry_date")
    return not expiry or date.fromisoformat(expiry) >= today


def _industry_match(policy: dict[str, Any], industry: str) -> bool:
    industries = set(policy.get("applicable_industries", []))
    return "全行业通用" in industries or industry in industries or "生活服务" in industries


def _rule_match(rule: dict[str, Any], application: ApplicationContext, score: AnalysisResult, material_count: int) -> bool:
    conditions = rule.get("conditions", {})
    if risk_bands := conditions.get("risk_bands"):
        if score.risk_band not in risk_bands:
            return False
    if decisions := conditions.get("decisions"):
        if score.decision not in decisions:
            return False
    if fund_uses := conditions.get("fund_uses"):
        if application.use_of_funds not in fund_uses:
            return False
    if material_count < conditions.get("min_material_count", 0):
        return False
    if score.dimensions.capacity < conditions.get("min_capacity_score", 0):
        return False
    if score.dimensions.online_reputation < conditions.get("min_reputation_score", 0):
        return False
    return True


def _select_bank_programs(policy: dict[str, Any], score: AnalysisResult) -> list[str]:
    programs = _load_json("bank_programs.json")["programs"]
    policy_tags = set(policy.get("purpose_tags", []))
    selected: list[str] = []
    for program in programs:
        if score.risk_band not in program.get("eligible_risk_bands", []):
            continue
        if not policy_tags.intersection(program.get("fit_tags", [])):
            continue
        selected.append(
            f"{program['program_name']}：{'; '.join(program.get('actions', [])[:3])}"
        )
    if not selected and score.risk_band in {"MEDIUM", "MANUAL_REVIEW"}:
        selected.append("合作平台曝光恢复与口碑修复：先小范围试点，观察评价、退款和投诉表现")
    return selected[:3]


def match_policy_recommendations(
    application: ApplicationContext,
    score: AnalysisResult,
    *,
    max_items: int = MAX_RECOMMENDATIONS,
) -> list[PolicyRecommendation]:
    policies = {item["policy_id"]: item for item in _load_json("policies.json")["policies"]}
    rules = _load_json("policy_rules.json")["rules"]
    industry = _normal_industry(application.industry)
    today = date.today()
    material_count = len(application.materials)
    candidates: list[tuple[int, PolicyRecommendation]] = []

    for rule in rules:
        policy = policies.get(rule["policy_id"])
        if not policy or not _is_current(policy, today):
            continue
        if not _industry_match(policy, industry):
            continue
        if not _rule_match(rule, application, score, material_count):
            continue

        status = policy.get("status", "ACTIVE")
        match_level = "HIGH" if rule.get("priority", 0) >= 90 and status == "ACTIVE" else "MEDIUM"
        if status == "DRAFT":
            match_level = "CANDIDATE"
        warnings = []
        if policy.get("local_confirmation_required"):
            warnings.append("需客户经理或运营人员核验地方口径、申报窗口和材料要求")
        if status == "DRAFT":
            warnings.append("模板政策仅作为候选，不应直接承诺可申请")
        if score.review_required:
            warnings.append("商户命中人工复核，政策申请建议同步转人工确认")

        bank_actions = [
            "协助核验适用条件与申报窗口",
            "整理授信、流水、用途和材料证据",
            "将活动核销、复购和投诉数据纳入后续监控",
        ]
        bank_actions.extend(_select_bank_programs(policy, score))

        candidates.append(
            (
                int(rule.get("priority", 0)),
                PolicyRecommendation(
                    policy_id=policy["policy_id"],
                    policy_name=policy["policy_name"],
                    policy_type=policy["policy_type"],
                    policy_level=policy["policy_level"],
                    support_method=policy["support_method"],
                    support_standard=policy["support_standard"],
                    match_level=match_level,
                    reason=rule.get("reason_template", policy["application_conditions"]),
                    required_materials=policy.get("required_materials", []),
                    application_steps=policy.get("application_process", []),
                    bank_actions=bank_actions[:6],
                    consumer_introduction=_select_bank_programs(policy, score),
                    source_url=policy.get("source_url"),
                    application_deadline=policy.get("application_deadline") or policy.get("expiry_date"),
                    status=status,
                    warnings=warnings,
                ),
            )
        )

    candidates.sort(key=lambda item: item[0], reverse=True)
    return [item for _, item in candidates[:max_items]]