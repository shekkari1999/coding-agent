#!/usr/bin/env bash
set -euo pipefail

MODEL="${MODEL:-Qwen/Qwen2.5-7B-Instruct}"

vllm serve "$MODEL" \
  --enable-prefix-caching \
  --disable-log-requests \
  --port 8000
