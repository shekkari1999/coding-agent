"""Run curated eval tasks."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from agent.graph import run_task
from agent.metrics import format_metrics_block

TASKS_DIR = Path(__file__).parent / "tasks"


def run_suite(baseline: bool = False) -> int:
    tasks = sorted(TASKS_DIR.glob("*.json"))
    if not tasks:
        print("No tasks in eval/tasks/")
        return 1

    mode = "baseline" if baseline else "optimized"
    print(f"Running {len(tasks)} task(s) in {mode} mode\n")

    passed = 0
    for path in tasks:
        spec = json.loads(path.read_text())
        name = spec["name"]
        repo = Path(spec["repo"])
        print(f"=== {name} ===")

        result, metrics = run_task(spec["task"], repo, baseline=baseline)
        ok = result["done"] and not result["stuck"]
        passed += int(ok)

        print(f"Result: {'pass' if ok else 'fail'}")
        print(format_metrics_block(metrics))
        print()

    print(f"Summary: {passed}/{len(tasks)} passed")
    return 0 if passed == len(tasks) else 2


if __name__ == "__main__":
    baseline_flag = "--baseline" in sys.argv
    raise SystemExit(run_suite(baseline=baseline_flag))
