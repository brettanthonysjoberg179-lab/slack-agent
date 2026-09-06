from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from slack_agent.client import lookup_channel, send_message
from slack_agent.models import SlackMessage, SlackResponse, ThreadReply

Command = Literal["send", "reply", "lookup_channel", "unknown"]


@dataclass(frozen=True)
class AgentCommand:
    kind: Command
    channel: str | None = None
    text: str | None = None
    thread_ts: str | None = None


class SlackAgent:
    def __init__(self, default_channel: str | None = None) -> None:
        self.default_channel = default_channel

    def send(self, message: SlackMessage) -> SlackResponse:
        return send_message(message)

    def post(self, text: str, channel: str | None = None) -> dict[str, object]:
        channel = channel or self.default_channel
        if not channel:
            raise ValueError("channel is required")
        response = send_message(SlackMessage(channel=channel, text=text))
        return {
            "ok": response.ok,
            "error": response.error,
            "command": "send",
            "channel": channel,
            "data": response.data,
        }

    def reply(self, text: str, channel: str, thread_ts: str) -> dict[str, object]:
        response = send_message(SlackMessage(channel=channel, text=text, thread_ts=thread_ts))
        return {
            "ok": response.ok,
            "error": response.error,
            "channel": channel,
            "thread_ts": thread_ts,
            "data": response.data,
        }

    def lookup_channel(self, name: str) -> dict[str, object]:
        response = lookup_channel(name)
        return {
            "ok": response.ok,
            "error": response.error,
            "channel": name,
            "data": response.data,
        }

    def handle(self, text: str) -> dict[str, object]:
        command = _parse(text)
        if command.kind == "send":
            channel = command.channel or self.default_channel
            if not channel:
                return {"ok": False, "error": "missing_channel", "command": "send"}
            return self.post(command.text or "", channel=channel)
        if command.kind == "reply":
            if not command.channel or not command.thread_ts or command.text is None:
                return {"ok": False, "error": "missing_reply_fields", "command": "reply"}
            return self.reply(command.text, command.channel, command.thread_ts)
        if command.kind == "lookup_channel":
            name = (command.channel or "").strip()
            if not name:
                return {"ok": False, "error": "missing_channel_name", "command": "lookup_channel"}
            return self.lookup_channel(name)
        return {"ok": False, "error": "unknown_command", "command": "unknown"}


_REPLY_RE = re.compile(r"^reply to (?P<channel>#[^ ]+)(?:\s+thread (?P<thread>[^ ]+))?:\s*(?P<text>.+)$", re.I)
_SEND_RE = re.compile(r"^send (?P<channel>#[^ ]+):\s*(?P<text>.+)$", re.I)
_LOOKUP_RE = re.compile(r"^lookup channel[:\s]+(?P<name>.+)$", re.I)


def _parse(text: str) -> AgentCommand:
    text = text.strip()
    reply = _REPLY_RE.match(text)
    if reply:
        return AgentCommand("reply", reply.group("channel"), reply.group("text"), reply.group("thread"))
    send = _SEND_RE.match(text)
    if send:
        return AgentCommand("send", send.group("channel"), send.group("text"), None)
    lookup = _LOOKUP_RE.match(text)
    if lookup:
        return AgentCommand("lookup_channel", lookup.group("name").strip(), None, None)
    return AgentCommand("unknown")
