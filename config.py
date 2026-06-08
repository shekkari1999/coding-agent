"""All tunable knobs in one place."""

import os
from pathlib import Path

# vLLM OpenAI-compatible API (override for RunPod: export VLLM_BASE_URL=...)
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
MODEL = os.getenv("VLLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")

# Agent limits
MAX_STEPS = 20
MAX_TEST_RETRIES = 3

# Default test command run after edits (override per task later)
DEFAULT_TEST_CMD = "pytest -x -q"

# Repo root defaults to cwd when you run `agent solve`
REPO_ROOT = Path(".")

# Prometheus metrics (defaults derived from VLLM_BASE_URL)
VLLM_METRICS_URL = os.getenv("VLLM_METRICS_URL", "")

# Nominal $/1M tokens for cost display (self-hosted: set to 0 or your estimate)
PROMPT_PRICE_PER_1M = float(os.getenv("PROMPT_PRICE_PER_1M", "0.10"))
COMPLETION_PRICE_PER_1M = float(os.getenv("COMPLETION_PRICE_PER_1M", "0.20"))
