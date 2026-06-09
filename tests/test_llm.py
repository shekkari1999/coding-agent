from unittest.mock import MagicMock, patch

import config
from agent import llm


def test_chat_sends_auth_header_when_api_key_set(monkeypatch):
    monkeypatch.setattr(config, "VLLM_API_KEY", "secret-key")
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
    mock_resp.raise_for_status = MagicMock()

    with patch("agent.llm.httpx.Client") as client_cls:
        client = client_cls.return_value.__enter__.return_value
        client.post.return_value = mock_resp

        assert llm.chat([{"role": "user", "content": "hi"}]) == "ok"
        _, kwargs = client.post.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer secret-key"
