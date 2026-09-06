from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from slack_agent.agent import SlackAgent, _parse
from slack_agent.client import lookup_channel, send_message
from slack_agent.models import SlackMessage, SlackResponse

logger = logging.getLogger(__name__)
agent = SlackAgent()


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("slack agent starting")
    yield
    logger.info("slack agent shutting down")


app = FastAPI(title="Slack Agent", lifespan=lifespan)


class MessageRequest(BaseModel):
    channel: str
    text: str
    thread_ts: str | None = None
    username: str | None = None
    icon_emoji: str | None = None


class PostResponse(BaseModel):
    ok: bool
    error: str | None = None
    data: dict | None = None
    channel: str


class ThreadResponse(BaseModel):
    ok: bool
    error: str | None = None
    thread_ts: str
    channel: str


class HandleRequest(BaseModel):
    text: str


class HandleResponse(BaseModel):
    ok: bool
    error: str | None = None
    command: str
    channel: str | None = None
    thread_ts: str | None = None
    data: dict | None = None


@app.post("/message", response_model=PostResponse)
def send_slack_message(request: MessageRequest) -> PostResponse:
    message = SlackMessage(
        channel=request.channel,
        text=request.text,
        thread_ts=request.thread_ts,
        username=request.username,
        icon_emoji=request.icon_emoji,
    )
    response = send_message(message)
    return PostResponse(
        ok=response.ok,
        error=response.error,
        data=response.data,
        channel=request.channel,
    )


@app.post("/reply", response_model=ThreadResponse)
def reply_to_slack_thread(request: MessageRequest) -> ThreadResponse:
    if not request.thread_ts:
        raise HTTPException(status_code=400, detail="thread_ts is required for replies")
    message = SlackMessage(
        channel=request.channel,
        text=request.text,
        thread_ts=request.thread_ts,
        username=request.username,
        icon_emoji=request.icon_emoji,
    )
    response = send_message(message)
    return ThreadResponse(
        ok=response.ok,
        error=response.error,
        thread_ts=request.thread_ts,
        channel=request.channel,
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/tools/post_message")
def tool_post_message(channel: str, text: str) -> dict:
    from slack_agent.tools import post_message

    return post_message(channel=channel, text=text)


@app.post("/tools/reply_to_thread")
def tool_reply_to_thread(channel: str, text: str, thread_ts: str) -> dict:
    from slack_agent.tools import reply_to_thread

    return reply_to_thread(channel=channel, text=text, thread_ts=thread_ts)


@app.post("/handle", response_model=HandleResponse)
def handle_prompt(request: HandleRequest) -> HandleResponse:
    result = agent.handle(request.text)
    return HandleResponse(
        ok=result.get("ok", False),
        error=result.get("error"),
        command=result.get("command", "unknown"),
        channel=result.get("channel"),
        thread_ts=result.get("thread_ts"),
        data=result.get("data"),
    )


@app.post("/channels/lookup")
def channels_lookup(name: str) -> dict:
    response = lookup_channel(name)
    return {
        "ok": response.ok,
        "error": response.error,
        "channel": name,
        "data": response.data,
    }


def run() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
