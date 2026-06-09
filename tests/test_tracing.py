from agent.tracing import is_enabled, project_name, status_line


def test_tracing_off_without_env(monkeypatch):
    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    assert not is_enabled()
    assert status_line() is None


def test_tracing_on_with_key(monkeypatch):
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGSMITH_API_KEY", "lsv2_test")
    monkeypatch.setenv("LANGSMITH_PROJECT", "my-project")
    assert is_enabled()
    assert project_name() == "my-project"
    assert "my-project" in status_line()
