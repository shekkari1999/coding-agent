"""All tunable knobs in one place."""

from pathlib import Path

# vLLM OpenAI-compatible API
VLLM_BASE_URL = "http://localhost:8000/v1"
MODEL = "Qwen/Qwen2.5-7B-Instruct"

# Agent limits
MAX_STEPS = 20
MAX_TEST_RETRIES = 3

# Default test command run after edits (override per task later)
DEFAULT_TEST_CMD = "pytest -x -q"

# Repo root defaults to cwd when you run `agent solve`
REPO_ROOT = Path(".")
