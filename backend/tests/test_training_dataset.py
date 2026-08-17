from __future__ import annotations

from training.build_dataset import build_examples, validate_examples


def test_seed_training_dataset_is_valid_and_covers_both_workflows() -> None:
    examples = build_examples()
    validate_examples(examples)

    tasks = {item["task"] for item in examples}
    assert tasks == {"workflow_assistant", "report_summary"}
    assert len(examples) >= 30
    assert sum(item["task"] == "report_summary" for item in examples) == 2
    assert any(
        item["source_id"].startswith("SAFE-")
        and '"should_escalate":true' in item["messages"][-1]["content"]
        for item in examples
    )

    report_input = next(
        item["messages"][1]["content"]
        for item in examples
        if item["task"] == "report_summary"
    )
    assert '"operating_credit_score"' in report_input
    assert '"material_evidence"' in report_input
    assert '"features"' not in report_input
