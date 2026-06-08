"""Thin client for vLLM's OpenAI-compatible API."""

from __future__ import annotations

import httpx

import config


def chat(messages: list[dict[str, str]], model: str | None = None) -> str:
    model = model or config.MODEL
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
    }
    url = f"{config.VLLM_BASE_URL.rstrip('/')}/chat/completions"
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
    return data["choices"][0]["message"]["content"]
