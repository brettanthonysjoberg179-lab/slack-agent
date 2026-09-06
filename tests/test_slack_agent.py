from __future__ import annotations

import os

import pytest
from slack_agent.models import SlackMessage, SlackResponse
from slack_agent.tools import post_message, reply_to_thread


def test_post_message_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    response = post_message(channel="#general", text="hello from tests")
    assert "ok" in response
    assert response["ok"] is False
    assert response["error"] == "missing_slack_bot_token"


def test_reply_to_thread_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    response = reply_to_thread(channel="#general", text="thread reply", thread_ts="12345")
    assert response["ok"] is False
    assert response["error"] == "missing_slack_bot_token"


def test_slack_message_defaults() -> None:
    message = SlackMessage(channel="#general", text="hi")
    assert message.channel == "#general"
    assert message.text == "hi"
    assert message.thread_ts is None
    assert message.blocks is None
