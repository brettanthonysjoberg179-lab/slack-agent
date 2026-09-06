from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

@dataclass
class SlackMessage:
    channel: str
    text: str
    thread_ts: str | None = None
    username: str | None = None
    icon_emoji: str | None = None
    blocks: list[dict[str, Any]] | None = None


@dataclass
class SlackResponse:
    ok: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
