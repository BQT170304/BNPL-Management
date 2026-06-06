from __future__ import annotations

from typing import Protocol

from app.modules.profiles.domain.entities import FinancialProfile


class ProfileRepository(Protocol):
    async def add(self, profile: FinancialProfile) -> None: ...
    async def get(self, profile_id: str) -> FinancialProfile: ...
    async def update(self, profile: FinancialProfile) -> None: ...
