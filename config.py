import os

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
VLLM_API_KEY = os.getenv("VLLM_API_KEY", "")
VLLM_MODEL = os.getenv("VLLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")

MAX_STEPS = 20

# LangSmith (optional): LANGSMITH_TRACING=true, LANGSMITH_API_KEY, LANGSMITH_PROJECT
