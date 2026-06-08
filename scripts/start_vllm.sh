#!/usr/bin/env bash
set -euo pipefail

MODEL="${MODEL:-Qwen/Qwen2.5-7B-Instruct}"

vllm serve "$MODEL" \
  --host 0.0.0.0 \
  --port 8000 \
  --enable-prefix-caching
