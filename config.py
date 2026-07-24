import os

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:8000/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "120"))

MAX_STEPS = 20

# LangSmith (optional): LANGSMITH_TRACING=true, LANGSMITH_API_KEY, LANGSMITH_PROJECT
