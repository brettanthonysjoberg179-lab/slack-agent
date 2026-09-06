from __future__ import annotations

import os
from typing import Any

import httpx

from slack_agent.models import SlackMessage, SlackResponse

SLACK_API_BASE = "https://slack.com/api"


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }


def send_message(message: SlackMessage, token: str | None = None) -> SlackResponse:
    token = token or os.environ.get("SLACK_BOT_TOKEN", "")
    if not token:
        return SlackResponse(ok=False, error="missing_slack_bot_token")

    payload: dict[str, Any] = {
        "channel": message.channel,
        "text": message.text,
    }
    if message.thread_ts:
        payload["thread_ts"] = message.thread_ts
    if message.username:
        payload["username"] = message.username
    if message.icon_emoji:
        payload["icon_emoji"] = message.icon_emoji
    if message.blocks:
        payload["blocks"] = message.blocks

    with httpx.Client(base_url=SLACK_API_BASE, headers=_headers(token), timeout=15) as client:
        resp = client.post("/chat.postMessage", json=payload)
        data = resp.json()

    return SlackResponse(
        ok=data.get("ok", False),
        data=data,
        error=data.get("error"),
    )
