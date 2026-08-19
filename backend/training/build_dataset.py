"""Build reproducible supervised fine-tuning data from reviewed project assets."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from app.schemas.ai import AiReportSummary, AssistantReply
from app.schemas.full_analysis import FullAnalysisResult
from app.services.report_context import build_report_context


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
KNOWLEDGE_ROOT = BACKEND_ROOT / "app" / "knowledge"
TRAINING_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = TRAINING_ROOT / "artifacts" / "dataset"
ASSISTANT_SYSTEM = (
    "你是五步授信流程助手，只解释经过审核的流程知识，不参与评分或授信决策。"
    "只返回符合 AssistantReply 契约的 JSON。"
)
REPORT_SYSTEM = (
    "你是授信分析结果解释器，只解释输入的 FullAnalysisResult，不修改评分、额度、"
    "异常、资金缺口或审核规则。只返回符合 AiReportSummary 契约的 JSON。"
)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _assistant_example(
    *,
    source_id: str,
    step: str,
    question: str,
    answer: str,
    evidence_refs: list[str] | None = None,
    should_escalate: bool = False,
) -> dict[str, Any]:
    output = AssistantReply(
        answer=answer,
        evidence_refs=evidence_refs or [source_id],
        should_escalate=should_escalate,
    )
    return {
        "task": "workflow_assistant",
        "source_id": source_id,
        "messages": [
            {"role": "system", "content": ASSISTANT_SYSTEM},
            {
                "role": "user",
                "content": json.dumps(
                    {"current_step": step, "question": question},
                    ensure_ascii=False,
                ),
            },
            {
                "role": "assistant",
                "content": output.model_dump_json(),
            },
        ],
    }


def build_examples() -> list[dict[str, Any]]:
    workflow = _load_json(KNOWLEDGE_ROOT / "workflow_faq.json")
    examples: list[dict[str, Any]] = []
    for entry in workflow["common"]:
        examples.append(
            _assistant_example(
                source_id=entry["id"],
                step="identity",
                question=entry["question"],
                answer=entry["answer"],
            )
        )
    for step, payload in workflow["steps"].items():
        for entry in payload["entries"]:
            examples.append(
                _assistant_example(
                    source_id=entry["id"],
                    step=step,
                    question=entry["question"],
                    answer=entry["answer"],
                )
            )

    materials = _load_json(KNOWLEDGE_ROOT / "material_requirements.json")
    for item in materials["requirements"]:
        examples.append(
            _assistant_example(
                source_id=item["id"],
                step="data",
                question=f"为什么需要{item['name']}，需要注意什么？",
                answer=f"{item['purpose']}{item['notice']}",
            )
        )

    scores = _load_json(KNOWLEDGE_ROOT / "score_explanations.json")
    for item in scores["entries"]:
        examples.append(
            _assistant_example(
                source_id=item["id"],
                step="results",
                question=f"{item['name']}是什么意思？",
                answer=item["explanation"],
            )
        )

    safety_examples = _load_json(TRAINING_ROOT / "data" / "safety_examples.json")
    for item in safety_examples:
        examples.append(
            _assistant_example(
                source_id=item["id"],
                step=item["step"],
                question=item["question"],
                answer=item["answer"],
                evidence_refs=item["evidence_refs"],
                should_escalate=item["should_escalate"],
            )
        )

    targets = _load_json(TRAINING_ROOT / "data" / "report_targets.json")
    for case_name in ("normal", "review"):
        path = REPO_ROOT / "docs" / "api_examples" / f"full_analysis_{case_name}_response.json"
        analysis = FullAnalysisResult.model_validate(_load_json(path))
        target = AiReportSummary.model_validate(targets[analysis.merchant_id])
        examples.append(
            {
                "task": "report_summary",
                "source_id": analysis.merchant_id,
                "messages": [
                    {"role": "system", "content": REPORT_SYSTEM},
                    {
                        "role": "user",
                        "content": json.dumps(
                            build_report_context(analysis),
                            ensure_ascii=False,
                            separators=(",", ":"),
                        ),
                    },
                    {"role": "assistant", "content": target.model_dump_json()},
                ],
            }
        )
    return examples


def validate_examples(examples: list[dict[str, Any]]) -> None:
    seen: set[tuple[str, str]] = set()
    for example in examples:
        if len(example["messages"]) != 3:
            raise ValueError("each seed example must contain system, user, assistant")
        key = (example["task"], example["source_id"])
        if key in seen:
            raise ValueError(f"duplicate training example: {key}")
        seen.add(key)
        answer = json.loads(example["messages"][-1]["content"])
        if example["task"] == "workflow_assistant":
            AssistantReply.model_validate(answer)
        elif example["task"] == "report_summary":
            AiReportSummary.model_validate(answer)
        else:
            raise ValueError(f"unknown task: {example['task']}")


def _write_jsonl(path: Path, examples: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in examples),
        encoding="utf-8",
    )


def write_dataset(output_dir: Path, seed: int = 20260815) -> dict[str, Any]:
    examples = build_examples()
    validate_examples(examples)
    shuffled = list(examples)
    random.Random(seed).shuffle(shuffled)
    eval_count = max(2, round(len(shuffled) * 0.2))
    train_examples = shuffled[eval_count:]
    eval_examples = shuffled[:eval_count]

    output_dir.mkdir(parents=True, exist_ok=True)
    train_path = output_dir / "train.jsonl"
    eval_path = output_dir / "eval.jsonl"
    _write_jsonl(train_path, train_examples)
    _write_jsonl(eval_path, eval_examples)
    digest = hashlib.sha256(train_path.read_bytes() + eval_path.read_bytes()).hexdigest()
    manifest = {
        "format_version": "icbc-sft-v1",
        "seed": seed,
        "train_examples": len(train_examples),
        "eval_examples": len(eval_examples),
        "tasks": sorted({item["task"] for item in examples}),
        "sha256": digest,
        "warning": "Seed data validates the pipeline; expand reviewed cases before claiming model quality.",
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seed", type=int, default=20260815)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        examples = build_examples()
        validate_examples(examples)
        counts = {
            task: sum(item["task"] == task for item in examples)
            for task in sorted({item["task"] for item in examples})
        }
        print(json.dumps({"valid": True, "examples": len(examples), "tasks": counts}, ensure_ascii=False))
        return
    print(json.dumps(write_dataset(args.output_dir, args.seed), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
