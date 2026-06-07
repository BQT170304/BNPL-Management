from __future__ import annotations

from app.core.errors import DecisionNotFound
from app.modules.decisions.domain.entities import DecisionTrace


class InMemoryDecisionRepository:
    def __init__(self) -> None:
        self._store: dict[str, DecisionTrace] = {}

    async def add(self, trace: DecisionTrace) -> None:
        self._store[trace.id] = trace

    async def get(self, decision_id: str) -> DecisionTrace:
        if decision_id not in self._store:
            raise DecisionNotFound(decision_id)
        return self._store[decision_id]

    async def update(self, trace: DecisionTrace) -> None:
        if trace.id not in self._store:
            raise DecisionNotFound(trace.id)
        self._store[trace.id] = trace
