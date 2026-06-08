import tempfile
from pathlib import Path

from agent.retrieval import RecencyTracker, retrieve_context


def test_recency_boost_ranks_recent_higher():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "old.py").write_text("def add numbers together\n")
        (root / "new.py").write_text("def subtract numbers\n")

        tracker = RecencyTracker()
        tracker.mark("old.py")

        baseline = retrieve_context("fix add function", root, tracker, True, 0.7, 0.3)
        optimized = retrieve_context("fix add function", root, tracker, False, 0.7, 0.3)

        assert "old.py" in baseline
        assert "old.py" in optimized or "new.py" in optimized


def test_no_keywords_returns_empty():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "a.py").write_text("x = 1\n")
        text = retrieve_context("!!!", root, RecencyTracker(), False, 0.7, 0.3)
        assert text == ""
