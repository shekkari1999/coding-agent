import httpx
from langsmith import traceable

import config


@traceable(run_type="llm", name="vllm_chat")
def chat(messages: list[dict[str, str]]) -> str:
    headers = {}
    if config.VLLM_API_KEY:
        headers["Authorization"] = f"Bearer {config.VLLM_API_KEY}"

    url = f"{config.VLLM_BASE_URL.rstrip('/')}/chat/completions"
    payload = {
        "model": config.VLLM_MODEL,
        "messages": messages,
        "temperature": 0.2,
    }
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
