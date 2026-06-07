from __future__ import annotations

from app.modules.feedback.domain.entities import Outcome


class InMemoryOutcomeRepository:
    """One current outcome per decision (re-recording updates it)."""

    def __init__(self) -> None:
        self._store: dict[str, Outcome] = {}

    async def upsert(self, outcome: Outcome) -> None:
        self._store[outcome.decision_id] = outcome

    async def get_for_decision(self, decision_id: str) -> Outcome | None:
        return self._store.get(decision_id)

    async def list_all(self) -> list[Outcome]:
        return sorted(self._store.values(), key=lambda o: o.recorded_at)
