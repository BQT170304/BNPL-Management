from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime

from app.modules.obligations.application.ports import ObligationRepository
from app.modules.obligations.domain.entities import Obligation
from app.modules.profiles.application.ports import ProfileRepository


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ObligationService:
    def __init__(
        self,
        obligations: ObligationRepository,
        profiles: ProfileRepository,
        now: Callable[[], datetime] = _utcnow,
    ) -> None:
        self._obligations = obligations
        self._profiles = profiles
        self._now = now

    async def add(self, obligation: Obligation) -> Obligation:
        await self._profiles.get(obligation.profile_id)
        await self._obligations.add(obligation)
        return obligation

    async def list_by_profile(self, profile_id: str) -> list[Obligation]:
        await self._profiles.get(profile_id)
        return await self._obligations.list_by_profile(profile_id)

    async def delete(self, profile_id: str, obligation_id: str) -> None:
        await self._profiles.get(profile_id)
        await self._obligations.delete(profile_id, obligation_id)

    async def verify(self, obligation_id: str, verified_by: str) -> Obligation:
        """Human verification: mark the obligation confirmed and promote its
        confidence to 1.0 so downstream decisions stop flagging it."""

        obligation = await self._obligations.get(obligation_id)
        verified = replace(
            obligation,
            confidence=1.0,
            verified_by=verified_by,
            verified_at=self._now(),
        )
        await self._obligations.update(verified)
        return verified
