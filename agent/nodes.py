"""LangGraph nodes: plan, execute, verify."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TypedDict

import config
from agent import llm, tools
from agent.retrieval import RecencyTracker, retrieve_context
from agent.router import select_model


class AgentState(TypedDict):
    task: str
    repo_root: str
    baseline: bool
    plan: str
    messages: list[dict[str, str]]
    last_tool_output: str
    last_tool: str
    files_touched: list[str]
    test_failures: int
    step_count: int
    last_test_output: str
    recency_step: int
    recency_paths: dict[str, int]
    done: bool
    stuck: bool


def plan_node(state: AgentState) -> AgentState:
    repo = Path(state["repo_root"])
    model = select_model(state)
    prompt = (
        f"You are a coding agent working in {repo}.\n"
        f"Task: {state['task']}\n"
        "Write a short step-by-step plan (3-6 bullets). No code yet."
    )
    plan = llm.chat([{"role": "user", "content": prompt}], model=model)

    tracker = _tracker_from_state(state)
    context = retrieve_context(
        state["task"],
        repo,
        tracker,
        state["baseline"],
        config.RELEVANCE_WEIGHT,
        config.RECENCY_WEIGHT,
    )
    user_content = f"Task: {state['task']}\n\nPlan:\n{plan}"
    if context:
        user_content += f"\n\nRelevant context:\n{context}"

    messages = [
        {
            "role": "system",
            "content": (
                "You are a coding agent. Use one tool per turn. "
                "Explore with read, grep, list before writing. "
                "After editing files, call done to run tests. "
                "Respond with a single JSON object only.\n"
                + tools.TOOL_DESCRIPTION
            ),
        },
        {"role": "user", "content": user_content},
    ]
    return {
        **state,
        "plan": plan,
        "messages": messages,
        "step_count": 0,
        "last_tool": "",
        **_tracker_to_state(tracker),
    }


def execute_node(state: AgentState) -> AgentState:
    step = state["step_count"] + 1
    if step > config.MAX_STEPS:
        return {
            **state,
            "step_count": step,
            "stuck": True,
            "done": True,
            "last_tool": "limit",
        }

    model = select_model(state)
    reply = llm.chat(state["messages"], model=model)
    action = _parse_action(reply)
    repo = Path(state["repo_root"])
    last_tool = "parse_error"
    tracker = _tracker_from_state(state)

    if action is None:
        result = tools.ToolResult(False, f"could not parse action from: {reply[:300]}")
    elif action.get("tool") == "done":
        result = tools.ToolResult(True, "ready to verify")
        last_tool = "done"
    else:
        last_tool = action.get("tool", "unknown")
        try:
            result = tools.dispatch(action["tool"], action, repo)
        except ValueError as exc:
            result = tools.ToolResult(False, str(exc))
        if result.ok and action.get("tool") == "read" and action.get("path"):
            tracker.mark(action["path"])

    files_touched = list(state["files_touched"])
    if action and action.get("tool") == "write" and result.ok:
        path = action.get("path")
        if path and path not in files_touched:
            files_touched.append(path)
        if path:
            tracker.mark(path)

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
        "last_tool_output": result.output,
        "last_tool": last_tool,
        "files_touched": files_touched,
        "step_count": step,
        **_tracker_to_state(tracker),
    }


def verify_node(state: AgentState) -> AgentState:
    repo = Path(state["repo_root"])
    result = tools.run_bash(config.DEFAULT_TEST_CMD, repo)

    if result.ok:
        return {
            **state,
            "last_test_output": result.output,
            "done": True,
            "stuck": False,
        }

    failures = state["test_failures"] + 1
    messages = state["messages"] + [
        {
            "role": "user",
            "content": (
                f"Tests failed (attempt {failures}):\n{result.output}\n"
                "Fix the issue with another tool call."
            ),
        },
    ]

    stuck = failures >= config.MAX_TEST_RETRIES
    return {
        **state,
        "messages": messages,
        "last_test_output": result.output,
        "test_failures": failures,
        "done": stuck,
        "stuck": stuck,
        "last_tool": "",
    }


def route_after_execute(state: AgentState) -> str:
    if state["done"] or state["stuck"]:
        return "finish"
    if state["last_tool"] in ("write", "done"):
        return "verify"
    return "execute"


def route_after_verify(state: AgentState) -> str:
    if state["done"]:
        return "finish"
    return "execute"


def _tracker_from_state(state: AgentState) -> RecencyTracker:
    return RecencyTracker(step=state["recency_step"], last_seen=dict(state["recency_paths"]))


def _tracker_to_state(tracker: RecencyTracker) -> dict:
    return {"recency_step": tracker.step, "recency_paths": tracker.last_seen}


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
    if "tool" not in data:
        return None
    return data
