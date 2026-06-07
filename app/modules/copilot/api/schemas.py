from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.modules.copilot.domain.reply import CopilotReply


class ChatIn(BaseModel):
    message: str = Field(min_length=1)
    profile_id: str | None = None
    decision_id: str | None = None


class ChatOut(BaseModel):
    reply: str
    tool: str
    used_optimizer: bool
    decision_id: str | None
    follow_up: str | None
    data: dict[str, Any]

    @classmethod
    def from_domain(cls, reply: CopilotReply) -> ChatOut:
        return cls(
            reply=reply.reply,
            tool=reply.tool.value,
            used_optimizer=reply.used_optimizer,
            decision_id=reply.decision_id,
            follow_up=reply.follow_up,
            data=reply.data,
        )
