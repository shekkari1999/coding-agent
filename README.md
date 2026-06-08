# coding-agent

Coding agent that plans, edits, runs tests, and retries on failure. Prints per-task cost and cache stats when done.

Same LangGraph loop as the baseline, with model routing and cache-aware retrieval turned on.

## How it works

```
you: agent solve "fix the off-by-one in parse_date"
         │
         ▼
    ┌─────────┐     ┌──────────┐     ┌─────────┐
    │  plan   │ -> │ edit/run │ -> │  tests  │
    └─────────┘     └──────────┘     └────┬────┘
         ▲                                │
         └-------- retry if fail --------┘
         │
         ▼
    print cost + cache stats
```

[LangGraph](https://github.com/langchain-ai/langgraph) for the loop. [vLLM](https://github.com/vllm-project/vllm) for inference.

| Model | When |
|-------|------|
| Qwen-7B | Planning, grep, small edits |
| Qwen-32B | After repeated test failures or large diffs |

## Quick start

Python 3.11+, GPU, model weights.

```bash
pip install -e .
./scripts/start_vllm.sh   # separate terminal
agent solve "add input validation to the signup form"
```

`--baseline` disables routing and cache-aware retrieval. Always uses Qwen-32B.

## Baseline vs optimized

| | Optimized | Baseline (`--baseline`) |
|---|-----------|------------------------|
| Model routing | 7B default, 32B when stuck | Always 32B |
| Retrieval | Relevance + recency boost | Semantic only |
| Everything else | Same graph, same tools | Same |

## Project layout

```
agent/
  graph.py      # the loop
  nodes.py      # plan, execute, verify, report
  tools.py      # read / write / grep / bash
  llm.py        # vLLM client
  metrics.py    # cost and cache numbers
  router.py     # 7B vs 32B
  retrieval.py  # context ranking
config.py
eval/
```

## Results

| | Baseline | Optimized |
|---|----------|-----------|
| Tasks solved | TBD | TBD |
| Avg cost / task | TBD | TBD |
| Avg latency | TBD | TBD |
| Cache hit rate | TBD | TBD |
