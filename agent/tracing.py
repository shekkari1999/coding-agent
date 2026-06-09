"""LangSmith tracing — opt-in via environment variables."""

from __future__ import annotations

import os

DEFAULT_PROJECT = "coding-agent"


def is_enabled() -> bool:
    if os.getenv("LANGSMITH_TRACING", "").lower() not in ("true", "1"):
        return False
    return bool(os.getenv("LANGSMITH_API_KEY"))


def project_name() -> str:
    return os.getenv("LANGSMITH_PROJECT", DEFAULT_PROJECT)


def status_line() -> str | None:
    if not is_enabled():
        return None
    return f"LangSmith tracing → project: {project_name()} (smith.langchain.com)"
