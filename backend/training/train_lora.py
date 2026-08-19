"""Train a real LoRA/QLoRA adapter on an open-weight DeepSeek distilled model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_BASE_MODEL = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
TRAINING_ROOT = Path(__file__).resolve().parent


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", default=DEFAULT_BASE_MODEL)
    parser.add_argument("--dataset-dir", type=Path, default=TRAINING_ROOT / "artifacts" / "dataset")
    parser.add_argument("--output-dir", type=Path, default=TRAINING_ROOT / "artifacts" / "adapter")
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation", type=int, default=8)
    parser.add_argument("--max-seq-length", type=int, default=8192)
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--load-in-4bit", action="store_true")
    return parser.parse_args()


def _tokenize(example: dict[str, Any], tokenizer: Any, max_length: int) -> dict[str, list[int]]:
    messages = example["messages"]
    full = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=False,
    )
    prompt = tokenizer.apply_chat_template(
        messages[:-1],
        tokenize=True,
        add_generation_prompt=True,
    )
    full = full[:max_length]
    prompt_length = min(len(prompt), len(full))
    labels = [-100] * prompt_length + full[prompt_length:]
    return {"input_ids": full, "attention_mask": [1] * len(full), "labels": labels}


def main() -> None:
    args = _arguments()
    train_file = args.dataset_dir / "train.jsonl"
    if not train_file.is_file():
        raise SystemExit("训练集不存在；请先运行 python -m training.build_dataset")

    import torch
    from datasets import load_dataset
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        DataCollatorForSeq2Seq,
        Trainer,
        TrainingArguments,
    )

    quantization_config = None
    if args.load_in_4bit:
        if not torch.cuda.is_available():
            raise SystemExit("--load-in-4bit 需要支持 bitsandbytes 的 CUDA 环境")
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
        )

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        trust_remote_code=True,
        device_map="auto",
        torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        quantization_config=quantization_config,
    )
    if args.load_in_4bit:
        model = prepare_model_for_kbit_training(model)
    model = get_peft_model(
        model,
        LoraConfig(
            task_type="CAUSAL_LM",
            r=args.lora_r,
            lora_alpha=args.lora_alpha,
            lora_dropout=args.lora_dropout,
            target_modules=[
                "q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj",
            ],
        ),
    )
    model.print_trainable_parameters()

    dataset = load_dataset("json", data_files={"train": str(train_file)})["train"]
    tokenized = dataset.map(
        lambda example: _tokenize(example, tokenizer, args.max_seq_length),
        remove_columns=dataset.column_names,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    trainer = Trainer(
        model=model,
        args=TrainingArguments(
            output_dir=str(args.output_dir),
            num_train_epochs=args.epochs,
            learning_rate=args.learning_rate,
            per_device_train_batch_size=args.batch_size,
            gradient_accumulation_steps=args.gradient_accumulation,
            logging_steps=1,
            save_strategy="epoch",
            report_to="none",
            remove_unused_columns=False,
            bf16=torch.cuda.is_available() and torch.cuda.is_bf16_supported(),
            fp16=torch.cuda.is_available() and not torch.cuda.is_bf16_supported(),
        ),
        train_dataset=tokenized,
        data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer, padding=True),
    )
    result = trainer.train()
    trainer.save_model(str(args.output_dir))
    tokenizer.save_pretrained(args.output_dir)
    (args.output_dir / "training_manifest.json").write_text(
        json.dumps(
            {
                "base_model": args.base_model,
                "dataset_dir": str(args.dataset_dir.resolve()),
                "train_samples": len(tokenized),
                "metrics": result.metrics,
                "artifact_type": "peft_lora_adapter",
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
