# coding-agent

CLI coding agent. You give it a task; it explores your repo, edits or creates files, and reports what it changed.

Inference runs on a GPU via [vLLM](https://github.com/vllm-project/vllm). The agent runs on your machine.

## What it does

1. **Plan** breaks the task into steps
2. **Act** runs one tool per turn: read, grep, list, write, bash
3. **Done** prints a summary

```
you: agent "add error handling to the signup form"
              │
              ▼
         ┌─────────┐
         │  plan   │
         └────┬────┘
              ▼
    read → grep → write → … → done
              │
              ▼
         Summary + files touched
```

## Quick start

**1. Install**

```bash
pip install -e .
```

**2. Start vLLM** on a GPU (local or cloud)

```bash
./scripts/start_vllm.sh
```

Remote GPU (e.g. vast.ai), tunnel to your Mac:

```bash
ssh -N -L 8001:127.0.0.1:8000 -p <PORT> root@<GPU_IP>
```

**3. Point the agent at it**

```bash
export VLLM_BASE_URL="http://localhost:8001/v1"
export VLLM_MODEL="Qwen/Qwen2.5-7B-Instruct"
```

**4. Run**

```bash
cd your-project
agent "fix the validation bug in signup.py"
```

Finds the git repo root from your cwd. Use `--repo` to override.

## Example output

```
Task: fix the validation bug in signup.py
Repo: /Users/you/your-project

Plan:
- Find signup validation code
- Fix the bug
- Summarize changes

Steps: 6
Files touched: signup.py

Summary:
Fixed email check to reject addresses without a domain dot.

Status: done
```

## LangSmith tracing

Set env vars to send traces to [LangSmith](https://smith.langchain.com):

```bash
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY="lsv2_..."
export LANGSMITH_PROJECT="coding-agent"
```

Each run logs graph nodes (`plan`, `execute`), LLM calls, and task metadata.

## Stack

- [LangGraph](https://github.com/langchain-ai/langgraph) for the plan/execute graph
- [vLLM](https://github.com/vllm-project/vllm) for GPU inference
- [LangSmith](https://smith.langchain.com) for tracing

## Project layout

```
agent/
  cli.py       # CLI entry point
  graph.py     # LangGraph wiring
  nodes.py     # plan + execute nodes
  tools.py     # read / write / grep / list / bash
  llm.py       # vLLM HTTP client
  repo.py      # git root detection
  tracing.py   # LangSmith helpers
config.py      # model, URL, step limit
scripts/
  start_vllm.sh
```
