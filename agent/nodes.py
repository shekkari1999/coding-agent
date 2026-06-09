import json
import re
from pathlib import Path
from typing import TypedDict

import config
from agent import llm, tools


class AgentState(TypedDict):
    task: str
    repo_root: str
    plan: str
    summary: str
    messages: list[dict[str, str]]
    files_touched: list[str]
    step_count: int
    done: bool
    stuck: bool


def plan_node(state: AgentState) -> AgentState:
    repo = Path(state["repo_root"])
    plan = llm.chat([
        {
            "role": "user",
            "content": (
                f"You are a coding agent in {repo}.\n"
                f"Task: {state['task']}\n"
                "Write a short plan (3-5 bullets). No code yet."
            ),
        }
    ])

    messages = [
        {
            "role": "system",
            "content": (
                "You are a coding agent. One tool per turn. "
                "Use read, grep, list to explore. Create or edit files with write. "
                "Call done with a summary when finished. "
                "Respond with a single JSON object only.\n"
                + tools.TOOL_DESCRIPTION
            ),
        },
        {"role": "user", "content": f"Task: {state['task']}\n\nPlan:\n{plan}"},
    ]
    return {**state, "plan": plan, "messages": messages, "step_count": 0}


def execute_node(state: AgentState) -> AgentState:
    step = state["step_count"] + 1
    if step > config.MAX_STEPS:
        return {
            **state,
            "step_count": step,
            "done": True,
            "stuck": True,
            "summary": "Stopped: step limit reached.",
        }

    reply = llm.chat(state["messages"])
    action = _parse_action(reply)
    repo = Path(state["repo_root"])
    finished = False
    summary = state.get("summary", "")

    if action is None:
        result = tools.ToolResult(False, f"could not parse: {reply[:300]}")
    elif action.get("tool") == "done":
        summary = action.get("message", "Done.")
        result = tools.ToolResult(True, summary)
        finished = True
    else:
        try:
            result = tools.dispatch(action["tool"], action, repo)
        except ValueError as exc:
            result = tools.ToolResult(False, str(exc))

    files_touched = list(state["files_touched"])
    if action and action.get("tool") == "write" and result.ok:
        path = action.get("path")
        if path and path not in files_touched:
            files_touched.append(path)

    messages = state["messages"] + [
        {"role": "assistant", "content": reply},
        {
            "role": "user",
            "content": f"Tool result ({'ok' if result.ok else 'error'}):\n{result.output}",
        },
    ]

    return {
        **state,
        "messages": messages,
        "files_touched": files_touched,
        "step_count": step,
        "done": finished,
        "summary": summary,
    }


def route_after_execute(state: AgentState) -> str:
    if state["done"] or state["stuck"]:
        return "finish"
    return "execute"


def _parse_action(text: str) -> dict | None:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group())
        except json.JSONDecodeError:
            return None
    return data if "tool" in data else None
