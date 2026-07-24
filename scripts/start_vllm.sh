#!/usr/bin/env bash
set -euo pipefail

MODEL="${LLM_MODEL:-Qwen/Qwen2.5-7B-Instruct}"

vllm serve "$MODEL" \
  --host 127.0.0.1 \
  --port 8000
