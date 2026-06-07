from __future__ import annotations

from fastapi import APIRouter, Depends

import app.dependencies as deps
from app.modules.copilot.api.schemas import ChatIn, ChatOut
from app.modules.copilot.application.services import CopilotService

router = APIRouter(tags=["copilot"])


def _service() -> CopilotService:
    # Indirection so tests can monkeypatch deps.get_copilot_service.
    return deps.get_copilot_service()


@router.post("/copilot/chat", response_model=ChatOut)
async def copilot_chat(
    body: ChatIn,
    service: CopilotService = Depends(_service),
) -> ChatOut:
    reply = await service.chat(
        body.message,
        profile_id=body.profile_id,
        decision_id=body.decision_id,
    )
    return ChatOut.from_domain(reply)
