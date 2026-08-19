"""Provider adapter for hosted DeepSeek, OpenAI, and local fine-tuned models."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, TypeVar

from pydantic import BaseModel

from app.settings import (
    ai_api_key,
    ai_base_url,
    ai_provider,
    ai_thinking_enabled,
    ai_timeout_seconds,
)

try:  # The deterministic parts of the app must boot without the optional SDK.
    from openai import OpenAI
except ImportError:  # pragma: no cover - only exercised in incomplete installs.
    OpenAI = None  # type: ignore[assignment,misc]


OutputT = TypeVar("OutputT", bound=BaseModel)


class LlmNotConfiguredError(RuntimeError):
    pass


class LlmOutputError(RuntimeError):
    pass


class LlmProviderError(RuntimeError):
    """A hosted-provider failure reduced to a safe, user-facing category."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class StructuredLlmResult:
    parsed: BaseModel
    response_id: str | None
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


def _client() -> Any:
    if OpenAI is None:
        raise LlmNotConfiguredError("OpenAI-compatible Python SDK is not installed")
    key = ai_api_key()
    provider = ai_provider()
    if provider != "local" and not key:
        raise LlmNotConfiguredError(f"{provider} API key is not configured")

    kwargs: dict[str, Any] = {
        "api_key": key or "local-model",
        "timeout": ai_timeout_seconds(),
    }
    if base_url := ai_base_url():
        kwargs["base_url"] = base_url
    if provider == "local" and "base_url" not in kwargs:
        raise LlmNotConfiguredError("ICBC_AI_BASE_URL is required for local models")
    return OpenAI(**kwargs)


def _chat_messages(messages: list[dict[str, str]], schema: type[BaseModel]) -> list[dict[str, str]]:
    """Convert OpenAI developer roles and append an explicit JSON contract."""

    converted: list[dict[str, str]] = []
    for message in messages:
        role = "system" if message["role"] == "developer" else message["role"]
        converted.append({"role": role, "content": message["content"]})

    schema_instruction = (
        "\n\n只返回一个 JSON 对象，不要使用 Markdown 代码块或补充说明。"
        "必须符合以下 JSON Schema：\n"
        + json.dumps(schema.model_json_schema(), ensure_ascii=False)
    )
    for message in converted:
        if message["role"] == "system":
            message["content"] += schema_instruction
            break
    else:
        converted.insert(0, {"role": "system", "content": schema_instruction.strip()})
    return converted


def _raise_provider_error(exc: Exception) -> None:
    """Avoid returning provider payloads or credentials to the browser."""

    status_code = getattr(exc, "status_code", None)
    class_name = type(exc).__name__.lower()
    if status_code in {401, 403}:
        reason = "authentication"
    elif status_code == 429:
        reason = "quota_or_rate_limit"
    elif "timeout" in class_name:
        reason = "timeout"
    elif "connection" in class_name:
        reason = "connection"
    else:
        reason = "provider_request"
    raise LlmProviderError(reason) from exc


def _enforce_top_level_array_limits(
    payload: Any, output_model: type[BaseModel]
) -> Any:
    """Apply schema presentation limits before strict Pydantic validation.

    JSON-mode providers occasionally return more list items than requested.
    Keeping the first allowed items is deterministic and does not alter any
    score, amount, evidence identifier, or individual generated statement.
    """

    if not isinstance(payload, dict):
        return payload
    properties = output_model.model_json_schema().get("properties", {})
    normalized = dict(payload)
    for field_name, field_schema in properties.items():
        max_items = field_schema.get("maxItems")
        value = normalized.get(field_name)
        if isinstance(max_items, int) and isinstance(value, list):
            normalized[field_name] = value[:max_items]
    return normalized


def generate_structured(
    *,
    model: str,
    messages: list[dict[str, str]],
    output_model: type[OutputT],
    max_output_tokens: int,
) -> StructuredLlmResult:
    """Generate and locally validate one structured response.

    OpenAI uses the SDK's schema parser. DeepSeek and local OpenAI-compatible
    servers use JSON mode followed by the same Pydantic validation, so model
    switching never weakens the application's validation boundary.
    """

    client = _client()
    provider = ai_provider()
    if provider == "openai":
        try:
            response = client.responses.parse(
                model=model,
                input=messages,
                text_format=output_model,
                max_output_tokens=max_output_tokens,
                store=False,
            )
        except Exception as exc:
            _raise_provider_error(exc)
        if response.output_parsed is None:
            raise LlmOutputError("provider returned no parsed output")
        return StructuredLlmResult(
            parsed=output_model.model_validate(response.output_parsed),
            response_id=getattr(response, "id", None),
            model=model,
        )

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": _chat_messages(messages, output_model),
        "response_format": {"type": "json_object"},
        "max_tokens": max_output_tokens,
    }
    if provider == "deepseek":
        kwargs["extra_body"] = {
            "thinking": {
                "type": "enabled" if ai_thinking_enabled() else "disabled"
            }
        }
    try:
        response = client.chat.completions.create(**kwargs)
    except Exception as exc:
        _raise_provider_error(exc)
    content = response.choices[0].message.content if response.choices else None
    if not content:
        raise LlmOutputError("provider returned empty JSON content")
    try:
        payload = _enforce_top_level_array_limits(json.loads(content), output_model)
        parsed = output_model.model_validate(payload)
    except (json.JSONDecodeError, ValueError) as exc:
        raise LlmOutputError("provider returned invalid structured output") from exc

    usage = getattr(response, "usage", None)
    return StructuredLlmResult(
        parsed=parsed,
        response_id=getattr(response, "id", None),
        model=model,
        prompt_tokens=getattr(usage, "prompt_tokens", None),
        completion_tokens=getattr(usage, "completion_tokens", None),
    )
