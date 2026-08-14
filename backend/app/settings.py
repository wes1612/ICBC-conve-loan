"""应用运行配置。"""

from __future__ import annotations

import os


DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


def cors_origins() -> list[str]:
    configured = os.getenv("ICBC_CORS_ORIGINS")
    if not configured:
        return list(DEFAULT_CORS_ORIGINS)
    return [origin.strip() for origin in configured.split(",") if origin.strip()]


def ai_api_key() -> str | None:
    """Return the server-only AI credential, if configured."""

    value = os.getenv("ICBC_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    return value.strip() if value and value.strip() else None


def ai_model() -> str:
    """Use one configurable model for both first-release AI workflows."""

    return os.getenv("ICBC_AI_MODEL", "gpt-5.6-terra").strip() or "gpt-5.6-terra"


def ai_base_url() -> str | None:
    value = os.getenv("ICBC_AI_BASE_URL")
    return value.strip().rstrip("/") if value and value.strip() else None


def ai_timeout_seconds() -> float:
    raw = os.getenv("ICBC_AI_TIMEOUT_SECONDS", "30")
    try:
        value = float(raw)
    except ValueError:
        return 30.0
    return min(max(value, 3.0), 120.0)

