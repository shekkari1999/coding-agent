"""CLI entry point: agent solve \"<task>\""""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agent.graph import run_task
from agent.metrics import format_metrics_block


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent")
    sub = parser.add_subparsers(dest="command", required=True)

    solve = sub.add_parser("solve", help="Run the agent on a task")
    solve.add_argument("task", help="What to do, in plain English")
    solve.add_argument(
        "--repo",
        type=Path,
        default=Path("."),
        help="Repo root (default: current directory)",
    )
    solve.add_argument(
        "--baseline",
        action="store_true",
        help="Baseline mode: always large model, no recency boost",
    )

    eval_parser = sub.add_parser("eval", help="Run the curated task suite")
    eval_parser.add_argument(
        "--baseline",
        action="store_true",
        help="Run in baseline mode",
    )

    args = parser.parse_args(argv)

    if args.command == "solve":
        return _solve(args.task, args.repo, args.baseline)
    if args.command == "eval":
        from eval.run import run_suite

        return run_suite(baseline=args.baseline)

    return 1


def _solve(task: str, repo: Path, baseline: bool) -> int:
    mode = "baseline" if baseline else "optimized"
    print(f"Task: {task}")
    print(f"Repo: {repo.resolve()}")
    print(f"Mode: {mode}\n")

    try:
        result, task_metrics = run_task(task, repo, baseline=baseline)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Plan:\n{result['plan']}\n")
    print(f"Steps: {result['step_count']}")
    print(f"Files touched: {', '.join(result['files_touched']) or 'none'}")
    print()
    print(format_metrics_block(task_metrics))

    if result["done"] and not result["stuck"]:
        print("\nStatus: resolved (tests passed)")
        return 0

    if result["stuck"]:
        print("\nStatus: stuck")
        if result["last_test_output"]:
            print(f"Last test output:\n{result['last_test_output']}")
        return 2

    print("\nStatus: stopped (step limit)")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
