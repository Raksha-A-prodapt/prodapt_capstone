from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
import requests

from llm.llm_client import (
    ANTHROPIC_MESSAGES_URL,
    DEFAULT_CLAUDE_MODEL,
    LLMClient,
)


def test_generate_uses_anthropic_messages_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("claude_api_key", "test-secret")
    monkeypatch.delenv("CLAUDE_MODEL", raising=False)
    client = LLMClient()
    response = Mock()
    response.json.return_value = {
        "content": [{"type": "text", "text": "Test reply"}],
    }

    with patch("llm.llm_client.requests.post", return_value=response) as post:
        answer = client.generate("System instruction", "Hello")

    assert answer == "Test reply"
    post.assert_called_once()
    args, kwargs = post.call_args
    assert args[0] == ANTHROPIC_MESSAGES_URL
    assert kwargs["headers"]["x-api-key"] == "test-secret"
    assert kwargs["json"]["model"] == DEFAULT_CLAUDE_MODEL
    assert kwargs["json"]["system"] == "System instruction"
    assert kwargs["json"]["messages"] == [
        {"role": "user", "content": "Hello"}
    ]


def test_generate_reports_http_status_without_exposing_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("claude_api_key", "test-secret")
    client = LLMClient()
    response = Mock()
    response.status_code = 401
    mocked_response = Mock()
    mocked_response.raise_for_status.side_effect = requests.HTTPError(
        response=response
    )

    with patch(
        "llm.llm_client.requests.post",
        return_value=mocked_response,
    ):
        with pytest.raises(RuntimeError, match="HTTP 401") as exc_info:
            client.generate("System instruction", "Hello")

    assert "test-secret" not in str(exc_info.value)
