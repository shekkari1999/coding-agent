#!/usr/bin/env bash
# Run this ON the RunPod GPU instance after SSH-ing in.
#
# Suggested pod: RTX 4090 or A40, 24GB+ VRAM, PyTorch template.
#
#   apt-get update && apt-get install -y git
#   pip install vllm
#   git clone https://github.com/shekkari1999/coding-agent
#   cd coding-agent && bash scripts/runpod_vllm.sh
#
# In RunPod: expose port 8000 (HTTP). Copy the public proxy URL, e.g.
#   https://<pod-id>-8000.proxy.runpod.net
#
# On your laptop (agent runs locally, inference remote):
#   export VLLM_BASE_URL="https://<pod-id>-8000.proxy.runpod.net/v1"
#   pip install -e .
#   agent solve "fix the failing test" --repo /path/to/project

set -euo pipefail

MODEL="${VLLM_MODEL:-Qwen/Qwen2.5-7B-Instruct}"

vllm serve "$MODEL" \
  --host 0.0.0.0 \
  --port 8000 \
  --enable-prefix-caching
