"""LangGraph wiring: plan -> execute -> verify -> (retry or done)."""

from __future__ import annotations

import time
from pathlib import Path

from langgraph.graph import END, StateGraph

import config
from agent.metrics import TaskMetrics, capture_metrics, compute_deltas
from agent.nodes import (
    AgentState,
    execute_node,
    plan_node,
    route_after_execute,
    route_after_verify,
    verify_node,
)


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("plan", plan_node)
    graph.add_node("execute", execute_node)
    graph.add_node("verify", verify_node)

    graph.set_entry_point("plan")
    graph.add_edge("plan", "execute")
    graph.add_conditional_edges(
        "execute",
        route_after_execute,
        {"execute": "execute", "verify": "verify", "finish": END},
    )
    graph.add_conditional_edges(
        "verify",
        route_after_verify,
        {"execute": "execute", "finish": END},
    )

    return graph.compile()


def run_task(
    task: str,
    repo_root: Path | None = None,
    baseline: bool = False,
) -> tuple[AgentState, TaskMetrics]:
    root = (repo_root or config.REPO_ROOT).resolve()
    initial: AgentState = {
        "task": task,
        "repo_root": str(root),
        "baseline": baseline,
        "plan": "",
        "messages": [],
        "last_tool_output": "",
        "last_tool": "",
        "files_touched": [],
        "test_failures": 0,
        "step_count": 0,
        "last_test_output": "",
        "recency_step": 0,
        "recency_paths": {},
        "done": False,
        "stuck": False,
    }
    before = capture_metrics()
    start = time.monotonic()
    result = build_graph().invoke(initial)
    duration_s = time.monotonic() - start
    after = capture_metrics()
    metrics = compute_deltas(before, after, duration_s)
    return result, metrics
