from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx

from slack_agent.models import SlackMessage, SlackResponse

SLACK_API_BASE = "https://slack.com/api"
MAX_RETRIES = 3
RETRY_BACKOFF = 0.5
TRANSIENT_ERRORS = {"ratelimited", "fatal_error", "account_inactive", "channel_not_found"}

logger = logging.getLogger(__name__)


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }


def _is_transient(error: str | None) -> bool:
    return error in TRANSIENT_ERRORS


def send_message(message: SlackMessage, token: str | None = None) -> SlackResponse:
    token = token or os.environ.get("SLACK_BOT_TOKEN", "")
    if not token:
        logger.error("Slack bot token missing")
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

    last_error: str | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with httpx.Client(base_url=SLACK_API_BASE, headers=_headers(token), timeout=15) as client:
                resp = client.post("/chat.postMessage", json=payload)
                data = resp.json()
            ok = data.get("ok", False)
            error = data.get("error")
            if ok or not _is_transient(error):
                return SlackResponse(ok=ok, data=data, error=error)
            last_error = error
            logger.warning("transient slack error on attempt %s: %s", attempt, error)
        except httpx.HTTPError as exc:
            logger.warning("http error on attempt %s: %s", attempt, exc)
            last_error = str(exc)
        if attempt < MAX_RETRIES:
            backoff = RETRY_BACKOFF * (2 ** (attempt - 1))
            time.sleep(backoff)

    return SlackResponse(ok=False, data={}, error=last_error or "unknown_error")


def lookup_channel(name: str, token: str | None = None) -> SlackResponse:
    token = token or os.environ.get("SLACK_BOT_TOKEN", "")
    if not token:
        return SlackResponse(ok=False, error="missing_slack_bot_token")

    try:
        with httpx.Client(base_url=SLACK_API_BASE, headers=_headers(token), timeout=15) as client:
            resp = client.get("/conversations.list", params={"types": "public_channel,private_channel", "limit": 200})
            data = resp.json()
    except httpx.HTTPError as exc:
        return SlackResponse(ok=False, error=str(exc))

    return SlackResponse(ok=data.get("ok", False), data=data, error=data.get("error"))
