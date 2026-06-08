"""All tunable knobs in one place."""

import os
from pathlib import Path

# vLLM OpenAI-compatible API
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
VLLM_METRICS_URL = os.getenv("VLLM_METRICS_URL", "")

MODEL_SMALL = os.getenv("VLLM_MODEL_SMALL", "Qwen/Qwen2.5-7B-Instruct")
MODEL_LARGE = os.getenv("VLLM_MODEL_LARGE", MODEL_SMALL)
MODEL = MODEL_SMALL  # backwards compat

# Agent limits
MAX_STEPS = 20
MAX_TEST_RETRIES = 3
ROUTER_FILE_THRESHOLD = 3

# Default test command run after edits
DEFAULT_TEST_CMD = "pytest -x -q"
REPO_ROOT = Path(".")

# Retrieval weights (baseline ignores recency)
RELEVANCE_WEIGHT = float(os.getenv("RELEVANCE_WEIGHT", "0.7"))
RECENCY_WEIGHT = float(os.getenv("RECENCY_WEIGHT", "0.3"))

# Cost display
GPU_PRICE_PER_HR = float(os.getenv("GPU_PRICE_PER_HR", "0.20"))
PROMPT_PRICE_PER_1M = float(os.getenv("PROMPT_PRICE_PER_1M", "0.10"))
COMPLETION_PRICE_PER_1M = float(os.getenv("COMPLETION_PRICE_PER_1M", "0.20"))
