from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


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

    @property
    def failed(self) -> bool:
        return not self.ok

    def raise_on_error(self) -> None:
        if self.failed:
            raise RuntimeError(f"Slack API error: {self.error}")


@dataclass
class ThreadReply:
    channel: str
    thread_ts: str
    text: str
    result: SlackResponse
