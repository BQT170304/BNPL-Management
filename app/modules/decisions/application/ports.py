from __future__ import annotations

from typing import Protocol

from app.modules.decisions.domain.entities import DecisionTrace


class DecisionRepository(Protocol):
    async def add(self, trace: DecisionTrace) -> None: ...
    async def get(self, decision_id: str) -> DecisionTrace: ...
    async def update(self, trace: DecisionTrace) -> None: ...
