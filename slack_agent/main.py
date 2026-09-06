from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from slack_agent.agent import SlackAgent
from slack_agent.client import send_message
from slack_agent.models import SlackMessage
from slack_agent.tools import post_message, reply_to_thread

app = FastAPI(title="Slack Agent")


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


@app.post("/message", response_model=PostResponse)
def send_slack_message(request: MessageRequest) -> PostResponse:
    message = SlackMessage(
        channel=request.channel,
        text=request.text,
        thread_ts=request.thread_ts,
        username=request.username,
        icon_emoji=request.icon_emoji,
    )
    agent = SlackAgent()
    result = agent.send(message)
    return PostResponse(
        ok=result["ok"],
        error=result.get("error"),
        data=result.get("data"),
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
    agent = SlackAgent()
    result = agent.send(message)
    return ThreadResponse(
        ok=result["ok"],
        error=result.get("error"),
        thread_ts=request.thread_ts,
        channel=request.channel,
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/tools/post_message")
def tool_post_message(channel: str, text: str) -> dict:
    return post_message(channel=channel, text=text)


@app.post("/tools/reply_to_thread")
def tool_reply_to_thread(channel: str, text: str, thread_ts: str) -> dict:
    return reply_to_thread(channel=channel, text=text, thread_ts=thread_ts)


def run() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
