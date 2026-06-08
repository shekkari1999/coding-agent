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

DEFAULT_TEST_CMD = "pytest -x -q"
REPO_ROOT = Path(".")

# Retrieval weights (baseline ignores recency)
RELEVANCE_WEIGHT = float(os.getenv("RELEVANCE_WEIGHT", "0.7"))
RECENCY_WEIGHT = float(os.getenv("RECENCY_WEIGHT", "0.3"))

# Token cost: amortize GPU $/hr across measured throughput (tokens/hr on your box)
GPU_PRICE_PER_HR = float(os.getenv("GPU_PRICE_PER_HR", "0.20"))
PREFILL_TOKENS_PER_HR = float(os.getenv("PREFILL_TOKENS_PER_HR", "600000"))
DECODE_TOKENS_PER_HR = float(os.getenv("DECODE_TOKENS_PER_HR", "180000"))

# Optional override: set both to use fixed $/1M instead of throughput-derived rates
PROMPT_PRICE_PER_1M = os.getenv("PROMPT_PRICE_PER_1M")
COMPLETION_PRICE_PER_1M = os.getenv("COMPLETION_PRICE_PER_1M")


def prefill_price_per_1m() -> float:
    if PROMPT_PRICE_PER_1M is not None:
        return float(PROMPT_PRICE_PER_1M)
    return GPU_PRICE_PER_HR / PREFILL_TOKENS_PER_HR * 1_000_000


def decode_price_per_1m() -> float:
    if COMPLETION_PRICE_PER_1M is not None:
        return float(COMPLETION_PRICE_PER_1M)
    return GPU_PRICE_PER_HR / DECODE_TOKENS_PER_HR * 1_000_000
