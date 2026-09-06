from __future__ import annotations

from slack_agent.client import send_message
from slack_agent.models import SlackMessage


def post_message(channel: str, text: str, **kwargs: object) -> dict[str, object]:
    message = SlackMessage(
        channel=channel,
        text=text,
        thread_ts=kwargs.get("thread_ts") if isinstance(kwargs.get("thread_ts"), str) else None,
        username=kwargs.get("username") if isinstance(kwargs.get("username"), str) else None,
        icon_emoji=kwargs.get("icon_emoji") if isinstance(kwargs.get("icon_emoji"), str) else None,
    )
    response = send_message(message)
    return {"ok": response.ok, "error": response.error, "data": response.data}


def reply_to_thread(channel: str, text: str, thread_ts: str) -> dict[str, object]:
    return post_message(channel=channel, text=text, thread_ts=thread_ts)
