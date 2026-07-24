import httpx
from langsmith import traceable

import config


@traceable(run_type="llm", name="llm_chat")
def chat(messages: list[dict[str, str]]) -> str:
    headers = {}
    if config.LLM_API_KEY:
        headers["Authorization"] = f"Bearer {config.LLM_API_KEY}"

    url = f"{config.LLM_BASE_URL.rstrip('/')}/chat/completions"
    payload = {
        "model": config.LLM_MODEL,
        "messages": messages,
        "temperature": 0.2,
    }
    with httpx.Client(timeout=config.LLM_TIMEOUT) as client:
        resp = client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
