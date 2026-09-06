from __future__ import annotations

from fastapi.testclient import TestClient

from slack_agent.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_send_message_missing_token() -> None:
    response = client.post("/message", json={"channel": "#general", "text": "hi"})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["error"] == "missing_slack_bot_token"


def test_reply_thread_validation() -> None:
    response = client.post("/reply", json={"channel": "#general", "text": "hi"})
    assert response.status_code == 400


def test_reply_thread_missing_token() -> None:
    response = client.post("/reply", json={"channel": "#general", "text": "hi", "thread_ts": "123"})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["thread_ts"] == "123"


def test_tool_post_message_missing_token() -> None:
    response = client.post("/tools/post_message", params={"channel": "#general", "text": "hi"})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["error"] == "missing_slack_bot_token"


def test_tool_reply_to_thread_missing_token() -> None:
    response = client.post(
        "/tools/reply_to_thread",
        params={"channel": "#general", "text": "hi", "thread_ts": "123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["error"] == "missing_slack_bot_token"
