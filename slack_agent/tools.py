from __future__ import annotations

from slack_agent.agent import SlackAgent
from slack_agent.client import lookup_channel, send_message
from slack_agent.models import SlackMessage, SlackResponse

__all__ = [
    "SlackAgent",
    "send_message",
    "lookup_channel",
    "SlackMessage",
    "SlackResponse",
]


def post_message(
    channel: str,
    text: str,
    *,
    thread_ts: str | None = None,
    username: str | None = None,
    icon_emoji: str | None = None,
) -> dict[str, object]:
    message = SlackMessage(
        channel=channel,
        text=text,
        thread_ts=thread_ts,
        username=username,
        icon_emoji=icon_emoji,
    )
    response = send_message(message)
    return {"ok": response.ok, "error": response.error, "data": response.data}


def reply_to_thread(channel: str, text: str, thread_ts: str) -> dict[str, object]:
    return post_message(channel=channel, text=text, thread_ts=thread_ts)
