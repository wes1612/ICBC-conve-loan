"""Minimal OpenAI-compatible server for the trained LoRA adapter.

This is intended for a controlled demo or evaluation environment. Production
deployments should use a hardened inference server such as vLLM.
"""

from __future__ import annotations

import os
from pathlib import Path
import time
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


DEFAULT_BASE_MODEL = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str = "icbc-credit-assistant"
    messages: list[ChatMessage] = Field(min_length=1)
    max_tokens: int = Field(default=1200, ge=1, le=8192)
    temperature: float | None = None
    response_format: dict[str, Any] | None = None


class Runtime:
    def __init__(self) -> None:
        self.model: Any | None = None
        self.tokenizer: Any | None = None

    def load(self) -> None:
        if self.model is not None:
            return
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer

        base_name = os.getenv("ICBC_TRAINED_BASE_MODEL", DEFAULT_BASE_MODEL)
        adapter_path = Path(
            os.getenv(
                "ICBC_TRAINED_ADAPTER",
                str(Path(__file__).resolve().parent / "artifacts" / "adapter"),
            )
        )
        if not adapter_path.is_dir():
            raise RuntimeError(f"LoRA adapter not found: {adapter_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(base_name, trust_remote_code=True)
        base = AutoModelForCausalLM.from_pretrained(
            base_name,
            trust_remote_code=True,
            device_map="auto",
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        )
        self.model = PeftModel.from_pretrained(base, adapter_path)
        self.model.eval()

    def generate(self, request: ChatRequest) -> tuple[str, int, int]:
        self.load()
        import torch

        assert self.model is not None and self.tokenizer is not None
        messages = [message.model_dump() for message in request.messages]
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        with torch.inference_mode():
            output = self.model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                do_sample=request.temperature is not None and request.temperature > 0,
                temperature=request.temperature or 1.0,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        generated = output[0, inputs["input_ids"].shape[1]:]
        content = self.tokenizer.decode(generated, skip_special_tokens=True).strip()
        return content, int(inputs["input_ids"].shape[1]), int(generated.shape[0])


runtime = Runtime()
app = FastAPI(title="ICBC trained model server", version="1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/models")
def models() -> dict[str, Any]:
    return {
        "object": "list",
        "data": [{"id": "icbc-credit-assistant", "object": "model", "owned_by": "local"}],
    }


@app.post("/v1/chat/completions")
def chat_completions(request: ChatRequest) -> dict[str, Any]:
    try:
        content, prompt_tokens, completion_tokens = runtime.generate(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "id": f"chatcmpl-{uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }
