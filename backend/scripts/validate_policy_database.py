"""Validate the file-backed policy database used by the MVP."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POLICY_DIR = ROOT / "data" / "policies"
REQUIRED_POLICY_FIELDS = {
    "policy_id",
    "policy_name",
    "issuer",
    "policy_level",
    "policy_type",
    "support_method",
    "support_standard",
    "applicable_industries",
    "applicable_subjects",
    "eligible_fund_uses",
    "required_materials",
    "application_process",
    "status",
    "updated_at",
}


def _load(name: str) -> dict:
    return json.loads((POLICY_DIR / name).read_text(encoding="utf-8"))


def main() -> None:
    payload = _load("policies.json")
    rules = _load("policy_rules.json")["rules"]
    policies = payload["policies"]
    ids = [item["policy_id"] for item in policies]
    errors: list[str] = []

    if len(ids) != len(set(ids)):
        errors.append("policy_id duplicated")
    for item in policies:
        missing = REQUIRED_POLICY_FIELDS - item.keys()
        if missing:
            errors.append(f"{item.get('policy_id', '<unknown>')} missing {sorted(missing)}")
        if item.get("status") == "ACTIVE" and not item.get("source_url"):
            errors.append(f"{item['policy_id']} ACTIVE policy must keep source_url")
        expiry = item.get("expiry_date")
        if expiry and date.fromisoformat(expiry) < date.today() and item.get("status") == "ACTIVE":
            errors.append(f"{item['policy_id']} expired but still ACTIVE")
    for rule in rules:
        if rule["policy_id"] not in ids:
            errors.append(f"{rule['rule_id']} references unknown policy {rule['policy_id']}")

    if errors:
        raise SystemExit("\n".join(errors))
    print(f"validated {len(policies)} policies and {len(rules)} rules in {POLICY_DIR}")


if __name__ == "__main__":
    main()