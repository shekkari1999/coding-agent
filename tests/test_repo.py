from pathlib import Path

from agent.repo import find_repo_root


def test_finds_git_root_from_subdirectory(tmp_path, monkeypatch):
    root = tmp_path / "project"
    sub = root / "src" / "pkg"
    sub.mkdir(parents=True)
    (root / ".git").mkdir()

    monkeypatch.chdir(sub)
    assert find_repo_root() == root.resolve()


def test_falls_back_to_cwd_without_git(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert find_repo_root() == tmp_path.resolve()
