# coding-agent

A small coding agent that tries to fix real tasks without burning money on inference.

Give it a task in plain English. It plans, reads your repo, edits files, runs tests, and retries if something breaks. When it's done, it prints what it cost — tokens, latency, cache hits — so you can see *why* it was cheap.

Built as a portfolio project: same agent as a naive baseline, but with smart model routing and cache-aware context retrieval. The goal is to show measurable wins (more tasks solved, less money spent), not to ship enterprise software.

## Why this exists

Most coding agents treat the LLM like a black box. You call it, you pay, you hope.

This one treats inference as something you can actually optimize:

- Use a **small model** for planning and search, **escalate to a big one** only when tests keep failing
- **Retrieve context** that's both relevant and likely already in the KV cache
- **Measure everything** per task with vLLM's Prometheus metrics

The interesting part isn't "I built an agent." It's "same agent, half the cost, here's the diff."

## How it works (short version)

```
you: agent solve "fix the off-by-one in parse_date"
         │
         ▼
    ┌─────────┐     ┌──────────┐     ┌─────────┐
    │  plan   │ ──▶ │ edit/run │ ──▶ │  tests  │
    └─────────┘     └──────────┘     └────┬────┘
         ▲                                │
         └──────── retry if fail ─────────┘
         │
         ▼
    print cost + cache stats
```

Under the hood that's a [LangGraph](https://github.com/langchain-ai/langgraph) loop — basically a state machine that keeps track of the plan, what files changed, and how many times tests failed.

Inference runs on [vLLM](https://github.com/vllm-project/vllm) locally. Two models:

| Model | When |
|-------|------|
| Qwen-7B | Default — planning, grep, small edits |
| Qwen-32B | Escalation — stuck after failed tests or big diffs |

## Quick start

**You'll need:** Python 3.11+, a GPU that can run vLLM, the model weights.

```bash
# 1. install
pip install -e .

# 2. start vLLM (separate terminal)
./scripts/start_vllm.sh

# 3. run a task
agent solve "add input validation to the signup form"
```

Add `--baseline` to run the comparison mode (no routing, no cache-aware retrieval, always the big model).

## Baseline vs optimized

| | Optimized | Baseline (`--baseline`) |
|---|-----------|------------------------|
| Model routing | 7B default, 32B when stuck | Always 32B |
| Retrieval | Relevance + recency boost | Semantic only |
| Everything else | Same graph, same tools | Same |

That's intentional. One variable at a time.

## Project layout

```
agent/
  graph.py      # the loop
  nodes.py      # plan, execute, verify, report
  tools.py      # read / write / grep / bash
  llm.py        # talks to vLLM
  metrics.py    # cost and cache numbers
  router.py     # 7B vs 32B
  retrieval.py  # what context to pull in
config.py       # all the knobs in one place
eval/           # task suite + runner
```

No microservices. No plugin architecture. One person should be able to read the whole thing in an afternoon.

## Results

> Not run yet — fill this in after your first eval.

| | Baseline | Optimized |
|---|----------|-----------|
| Tasks solved | — | — |
| Avg cost / task | — | — |
| Avg latency | — | — |
| Cache hit rate | — | — |

## What I'm not claiming

- SOTA on SWE-bench (that's not the point)
- Production-ready agent framework
- Perfect knowledge of what's in the KV cache (v1 uses a simple recency heuristic)

## Stack

Python · LangGraph · vLLM · Qwen-7B/32B · rich

---

*Work in progress. If something's unclear, that's a bug in the code or the README — not you.*
