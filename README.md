# coding-agent

CLI coding agent: plan, use tools on a repo, report what it did.

```
agent "fix the login bug"
     │
     ▼
  plan → read / grep / write → done
```

Built with [LangGraph](https://github.com/langchain-ai/langgraph). Inference via [vLLM](https://github.com/vllm-project/vllm). Optional tracing via [LangSmith](https://smith.langchain.com).

## Setup

```bash
pip install -e .
export VLLM_BASE_URL="http://localhost:8000/v1"
export VLLM_MODEL="Qwen/Qwen2.5-7B-Instruct"
```

Start vLLM on a GPU (local or remote), or tunnel to a cloud instance:

```bash
./scripts/start_vllm.sh
```

## LangSmith tracing

Set env vars to trace every run in the [LangSmith UI](https://smith.langchain.com):

```bash
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY="lsv2_..."
export LANGSMITH_PROJECT="coding-agent"
```

Each `agent` run shows:

- **Graph trace** — `plan` and `execute` nodes, step-by-step
- **LLM calls** — each `vllm_chat` span with prompts and responses
- **Metadata** — task text, repo path, tags

No code changes needed beyond the env vars.

## Usage

```bash
cd your-project
agent "add input validation to the signup form"
```

Runs from anywhere inside a git repo — uses the repo root automatically.

```bash
agent "refactor auth.py" --repo /path/to/other/project
```

## Layout

```
agent/
  cli.py      # entry point
  graph.py    # LangGraph loop
  nodes.py    # plan + execute
  tools.py    # read / write / grep / list / bash
  llm.py      # vLLM client
  repo.py     # find git root
  tracing.py  # LangSmith helpers
config.py
```
