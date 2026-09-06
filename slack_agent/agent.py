from __future__ import annotations

from slack_agent.models import SlackMessage
from slack_agent.client import send_message


class SlackAgent:
    def __init__(self, default_channel: str | None = None) -> None:
        self.default_channel = default_channel

    def send(self, message: SlackMessage) -> dict[str, object]:
        response = send_message(message)
        return {
            "ok": response.ok,
            "error": response.error,
            "channel": message.channel,
            "data": response.data,
        }

    def post(self, text: str, channel: str | None = None) -> dict[str, object]:
        channel = channel or self.default_channel
        if not channel:
            raise ValueError("channel is required")
        return self.send(SlackMessage(channel=channel, text=text))
