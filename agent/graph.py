from pathlib import Path

import langsmith as ls
from langgraph.graph import END, StateGraph

from agent.nodes import AgentState, execute_node, plan_node, route_after_execute
from agent.tracing import is_enabled, project_name


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("plan", plan_node)
    graph.add_node("execute", execute_node)
    graph.set_entry_point("plan")
    graph.add_edge("plan", "execute")
    graph.add_conditional_edges(
        "execute",
        route_after_execute,
        {"execute": "execute", "finish": END},
    )
    return graph.compile()


def run_task(task: str, repo_root: Path) -> AgentState:
    initial: AgentState = {
        "task": task,
        "repo_root": str(repo_root.resolve()),
        "plan": "",
        "summary": "",
        "messages": [],
        "files_touched": [],
        "step_count": 0,
        "done": False,
        "stuck": False,
    }
    run_config = {
        "run_name": task[:100],
        "metadata": {"task": task, "repo": str(repo_root.resolve())},
        "tags": ["coding-agent"],
    }
    graph = build_graph()

    if is_enabled():
        with ls.tracing_context(project_name=project_name(), enabled=True):
            return graph.invoke(initial, config=run_config)

    return graph.invoke(initial, config=run_config)
