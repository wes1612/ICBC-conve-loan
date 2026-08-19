"""应用运行配置。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv


# Local development reads the repository-level .env file. Existing process
# environment variables still win, which keeps deployment configuration and
# secret injection predictable.
REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env", override=False)


DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
)


def cors_origins() -> list[str]:
    configured = os.getenv("ICBC_CORS_ORIGINS")
    if not configured:
        return list(DEFAULT_CORS_ORIGINS)
    return [origin.strip() for origin in configured.split(",") if origin.strip()]


AiProvider = Literal["deepseek", "openai", "local"]


def ai_provider() -> AiProvider:
    """Return the selected inference provider.

    ``local`` means an OpenAI-compatible server such as vLLM that serves a
    locally fine-tuned adapter or merged model.
    """

    value = os.getenv("ICBC_AI_PROVIDER", "deepseek").strip().lower()
    if value not in {"deepseek", "openai", "local"}:
        return "deepseek"
    return value  # type: ignore[return-value]


def ai_api_key() -> str | None:
    """Return the server-only AI credential, if configured."""

    value = os.getenv("ICBC_AI_API_KEY")
    if not value and ai_provider() == "deepseek":
        value = os.getenv("DEEPSEEK_API_KEY")
    if not value and ai_provider() == "openai":
        value = os.getenv("ICBC_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    return value.strip() if value and value.strip() else None


def ai_model() -> str:
    """Use one configurable model for both AI workflows by default."""

    defaults = {
        "deepseek": "deepseek-v4-flash",
        "openai": "gpt-5.6-terra",
        "local": "icbc-credit-assistant",
    }
    default = defaults[ai_provider()]
    return os.getenv("ICBC_AI_MODEL", default).strip() or default


def ai_assistant_model() -> str:
    return os.getenv("ICBC_AI_ASSISTANT_MODEL", ai_model()).strip() or ai_model()


def ai_report_model() -> str:
    return os.getenv("ICBC_AI_REPORT_MODEL", ai_model()).strip() or ai_model()


def ai_base_url() -> str | None:
    value = os.getenv("ICBC_AI_BASE_URL")
    if value and value.strip():
        return value.strip().rstrip("/")
    if ai_provider() == "deepseek":
        return "https://api.deepseek.com"
    return None


def ai_thinking_enabled() -> bool:
    value = os.getenv("ICBC_AI_THINKING", "false").strip().lower()
    return value in {"1", "true", "yes", "on"}


def ai_max_output_tokens(workflow: Literal["assistant", "report"]) -> int:
    env_name = (
        "ICBC_AI_ASSISTANT_MAX_TOKENS"
        if workflow == "assistant"
        else "ICBC_AI_REPORT_MAX_TOKENS"
    )
    default = 1200 if workflow == "assistant" else 2200
    raw = os.getenv(env_name, str(default))
    try:
        value = int(raw)
    except ValueError:
        return default
    return min(max(value, 128), 8192)


def ai_timeout_seconds() -> float:
    raw = os.getenv("ICBC_AI_TIMEOUT_SECONDS", "30")
    try:
        value = float(raw)
    except ValueError:
        return 30.0
    return min(max(value, 3.0), 120.0)


def ai_is_configured() -> bool:
    if ai_provider() == "local":
        return ai_base_url() is not None
    return ai_api_key() is not None

