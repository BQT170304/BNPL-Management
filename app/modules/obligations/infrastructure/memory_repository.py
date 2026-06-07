from __future__ import annotations

from app.core.errors import ObligationNotFound
from app.modules.obligations.domain.entities import Obligation


class InMemoryObligationRepository:
    def __init__(self) -> None:
        self._store: dict[str, Obligation] = {}

    async def add(self, obligation: Obligation) -> None:
        self._store[obligation.id] = obligation

    async def get(self, obligation_id: str) -> Obligation:
        if obligation_id not in self._store:
            raise ObligationNotFound(obligation_id)
        return self._store[obligation_id]

    async def update(self, obligation: Obligation) -> None:
        if obligation.id not in self._store:
            raise ObligationNotFound(obligation.id)
        self._store[obligation.id] = obligation

    async def list_by_profile(self, profile_id: str) -> list[Obligation]:
        return sorted(
            (o for o in self._store.values() if o.profile_id == profile_id),
            key=lambda o: (o.start_date, o.due_day, o.id),
        )

    async def delete(self, profile_id: str, obligation_id: str) -> None:
        obligation = self._store.get(obligation_id)
        if obligation is None or obligation.profile_id != profile_id:
            raise ObligationNotFound(obligation_id)
        del self._store[obligation_id]
