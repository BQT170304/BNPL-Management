from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.modules.copilot.domain.intents import CopilotTool


@dataclass(frozen=True)
class CopilotReply:
    reply: str
    tool: CopilotTool
    used_optimizer: bool = False
    decision_id: str | None = None
    follow_up: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
