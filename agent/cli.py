import argparse
import sys
from pathlib import Path

from agent.graph import run_task
from agent.repo import find_repo_root
from agent.tracing import status_line


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent", description="Coding agent")
    parser.add_argument("task", help="What to do")
    parser.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="Repo root (default: git root of cwd, else cwd)",
    )
    args = parser.parse_args(argv)

    repo = (args.repo or find_repo_root()).resolve()
    print(f"Task: {args.task}")
    print(f"Repo: {repo}")
    if line := status_line():
        print(line)
    print()

    try:
        result = run_task(args.task, repo)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Plan:\n{result['plan']}\n")
    print(f"Steps: {result['step_count']}")
    print(f"Files touched: {', '.join(result['files_touched']) or 'none'}")
    if result.get("summary"):
        print(f"\nSummary:\n{result['summary']}")

    if result["done"] and not result["stuck"]:
        print("\nStatus: done")
        return 0
    print("\nStatus: stopped")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
