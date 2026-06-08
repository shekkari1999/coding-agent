"""Context retrieval: keyword relevance + optional recency boost."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RecencyTracker:
    step: int = 0
    last_seen: dict[str, int] = field(default_factory=dict)

    def mark(self, path: str) -> None:
        self.step += 1
        self.last_seen[path] = self.step

    def score(self, path: str) -> float:
        if self.step == 0 or path not in self.last_seen:
            return 0.0
        return self.last_seen[path] / self.step


def retrieve_context(
    task: str,
    repo_root: Path,
    tracker: RecencyTracker,
    baseline: bool,
    relevance_weight: float,
    recency_weight: float,
    max_chunks: int = 3,
) -> str:
    keywords = _keywords(task)
    if not keywords:
        return ""

    root = repo_root.resolve()
    candidates: list[tuple[str, str, float, float]] = []
    for path in _python_files(root):
        try:
            text = path.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        rel = str(path.resolve().relative_to(root))
        relevance = _relevance(keywords, text)
        if relevance <= 0:
            continue
        recency = 0.0 if baseline else tracker.score(rel)
        candidates.append((rel, text[:800], relevance, recency))

    if not candidates:
        return ""

    scored = sorted(
        candidates,
        key=lambda c: relevance_weight * c[2] + recency_weight * c[3],
        reverse=True,
    )[:max_chunks]

    parts = []
    for rel, snippet, _, _ in scored:
        parts.append(f"--- {rel} ---\n{snippet}")
    return "\n\n".join(parts)


def _keywords(task: str) -> set[str]:
    words = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{2,}", task.lower())
    stop = {"the", "and", "for", "fix", "that", "with", "this", "from", "pass", "test"}
    return {w for w in words if w not in stop}


def _relevance(keywords: set[str], text: str) -> float:
    lower = text.lower()
    hits = sum(lower.count(w) for w in keywords)
    return hits / max(len(keywords), 1)


def _python_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    root = repo_root.resolve()
    for path in root.rglob("*.py"):
        if any(p in {".git", "__pycache__", ".venv", "node_modules"} for p in path.parts):
            continue
        files.append(path)
        if len(files) >= 40:
            break
    return files
