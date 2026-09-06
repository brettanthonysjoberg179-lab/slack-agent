from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from slack_agent.agent import _parse, SlackAgent
from slack_agent.client import send_message, lookup_channel
from slack_agent.models import SlackMessage, SlackResponse
from slack_agent.tools import post_message, reply_to_thread
from slack_agent.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_send_message_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    response = client.post("/message", json={"channel": "#general", "text": "hi"})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["error"] == "missing_slack_bot_token"


def test_reply_thread_validation() -> None:
    response = client.post("/reply", json={"channel": "#general", "text": "hi"})
    assert response.status_code == 400


def test_reply_thread_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    response = client.post("/reply", json={"channel": "#general", "text": "hi", "thread_ts": "123"})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["thread_ts"] == "123"


def test_tool_post_message_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    response = client.post("/tools/post_message", params={"channel": "#general", "text": "hi"})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["error"] == "missing_slack_bot_token"


def test_tool_reply_to_thread_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    response = client.post(
        "/tools/reply_to_thread",
        params={"channel": "#general", "text": "hi", "thread_ts": "123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["error"] == "missing_slack_bot_token"


def test_handle_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    response = client.post("/handle", json={"text": "send #general: hello"})
    assert response.status_code == 200
    body = response.json()
    assert body["command"] == "send"
    assert body["channel"] == "#general"
    assert body["ok"] is False
    assert body["error"] == "missing_slack_bot_token"


def test_channels_lookup_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    response = client.post("/channels/lookup", params={"name": "general"})
    assert response.status_code == 200
    body = response.json()
    assert body["channel"] == "general"
    assert body["ok"] is False
    assert body["error"] == "missing_slack_bot_token"


def test_slack_response_helpers() -> None:
    failed = SlackResponse(ok=False, error="boom")
    assert failed.failed is True
    with pytest.raises(RuntimeError):
        failed.raise_on_error()

    ok = SlackResponse(ok=True, data={"channel": "C1"})
    assert ok.failed is False
    ok.raise_on_error()


def test_send_message_retries_on_transient() -> None:
    responses = [
        {"ok": False, "error": "ratelimited"},
        {"ok": True, "channel": "C1"},
    ]
    with patch("slack_agent.client.httpx.Client") as MockClient:
        client_instance = MockClient.return_value.__enter__.return_value
        client_instance.post.return_value.json.side_effect = responses
        response = send_message(SlackMessage(channel="#general", text="hi"), token="x")
        assert response.ok is True
        assert client_instance.post.call_count == 2


def test_lookup_channel_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    response = lookup_channel("general")
    assert response.ok is False
    assert response.error == "missing_slack_bot_token"


def test_parse_commands() -> None:
    assert _parse("send #general: hello").kind == "send"
    assert _parse("reply to #general thread 123: hi").kind == "reply"
    assert _parse("lookup channel: general").kind == "lookup_channel"
    assert _parse("random").kind == "unknown"


def test_agent_handle_send_requires_channel() -> None:
    agent = SlackAgent()
    result = agent.handle("send: hello")
    assert result["ok"] is False
    assert result["error"] == "unknown_command"


def test_agent_handle_reply_requires_fields() -> None:
    agent = SlackAgent()
    result = agent.handle("reply to #general: hi")
    assert result["ok"] is False
    assert result["error"] == "missing_reply_fields"


def test_agent_handle_lookup_requires_name() -> None:
    agent = SlackAgent()
    result = agent.handle("lookup channel:")
    assert result["ok"] is False
    assert result["error"] == "unknown_command"


def test_lookup_channel_with_token() -> None:
    responses = [{"ok": True, "channels": [{"name": "general", "id": "C1"}]}]
    with patch("slack_agent.client.httpx.Client") as MockClient:
        client_instance = MockClient.return_value.__enter__.return_value
        client_instance.get.return_value.json.side_effect = responses
        response = lookup_channel("general", token="x")
    assert response.ok is True
    assert response.data["channels"][0]["id"] == "C1"
