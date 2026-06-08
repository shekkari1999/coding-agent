"""File and shell tools the agent can call."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ToolResult:
    ok: bool
    output: str


def read_file(path: str, repo_root: Path) -> ToolResult:
    target = _resolve(path, repo_root)
    if not target.is_file():
        return ToolResult(False, f"file not found: {path}")
    try:
        text = target.read_text()
    except UnicodeDecodeError:
        return ToolResult(False, f"not a text file: {path}")
    return ToolResult(True, text)


def write_file(path: str, content: str, repo_root: Path) -> ToolResult:
    target = _resolve(path, repo_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    return ToolResult(True, f"wrote {path} ({len(content)} bytes)")


def grep(pattern: str, repo_root: Path, path: str = ".") -> ToolResult:
    target = _resolve(path, repo_root)
    try:
        regex = re.compile(pattern)
    except re.error as exc:
        return ToolResult(False, f"invalid regex: {exc}")

    hits: list[str] = []
    search_root = target if target.is_dir() else target.parent
    for file in search_root.rglob("*"):
        if not file.is_file() or _skip(file):
            continue
        try:
            for i, line in enumerate(file.read_text().splitlines(), start=1):
                if regex.search(line):
                    rel = file.relative_to(repo_root.resolve())
                    hits.append(f"{rel}:{i}:{line}")
        except (UnicodeDecodeError, OSError):
            continue
        if len(hits) >= 50:
            break

    if not hits:
        return ToolResult(True, "no matches")
    return ToolResult(True, "\n".join(hits))


def run_bash(command: str, repo_root: Path, timeout: int = 120) -> ToolResult:
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return ToolResult(False, f"timed out after {timeout}s")

    out = (proc.stdout + proc.stderr).strip() or "(no output)"
    return ToolResult(proc.returncode == 0, out)


def list_dir(path: str, repo_root: Path) -> ToolResult:
    target = _resolve(path, repo_root)
    if not target.is_dir():
        return ToolResult(False, f"not a directory: {path}")
    entries = sorted(p.name + ("/" if p.is_dir() else "") for p in target.iterdir())
    return ToolResult(True, "\n".join(entries))


def dispatch(tool: str, args: dict, repo_root: Path) -> ToolResult:
    if tool == "read":
        return read_file(args["path"], repo_root)
    if tool == "write":
        return write_file(args["path"], args["content"], repo_root)
    if tool == "grep":
        return grep(args["pattern"], repo_root, args.get("path", "."))
    if tool == "bash":
        return run_bash(args["command"], repo_root)
    if tool == "list":
        return list_dir(args.get("path", "."), repo_root)
    return ToolResult(False, f"unknown tool: {tool}")


TOOL_DESCRIPTION = """Available tools (respond with JSON only):
- {"tool":"read","path":"relative/path.py"}
- {"tool":"write","path":"relative/path.py","content":"..."}
- {"tool":"grep","pattern":"regex","path":"."}
- {"tool":"list","path":"."}
- {"tool":"bash","command":"shell command"}
"""


def _resolve(path: str, repo_root: Path) -> Path:
    root = repo_root.resolve()
    target = (root / path).resolve()
    if root not in target.parents and target != root:
        raise ValueError(f"path escapes repo: {path}")
    return target


def _skip(path: Path) -> bool:
    parts = path.parts
    return any(p in {".git", "__pycache__", ".venv", "node_modules"} for p in parts)
