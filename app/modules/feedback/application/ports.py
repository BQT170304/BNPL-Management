from __future__ import annotations

from typing import Protocol

from app.modules.feedback.domain.entities import Outcome


class OutcomeRepository(Protocol):
    async def upsert(self, outcome: Outcome) -> None: ...
    async def get_for_decision(self, decision_id: str) -> Outcome | None: ...
    async def list_all(self) -> list[Outcome]: ...
