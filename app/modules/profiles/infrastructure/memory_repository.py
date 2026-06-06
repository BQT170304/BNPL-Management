from __future__ import annotations

from app.core.errors import ProfileNotFound
from app.modules.profiles.domain.entities import FinancialProfile


class InMemoryProfileRepository:
    def __init__(self) -> None:
        self._store: dict[str, FinancialProfile] = {}

    async def add(self, profile: FinancialProfile) -> None:
        self._store[profile.id] = profile

    async def get(self, profile_id: str) -> FinancialProfile:
        if profile_id not in self._store:
            raise ProfileNotFound(profile_id)
        return self._store[profile_id]

    async def update(self, profile: FinancialProfile) -> None:
        if profile.id not in self._store:
            raise ProfileNotFound(profile.id)
        self._store[profile.id] = profile
