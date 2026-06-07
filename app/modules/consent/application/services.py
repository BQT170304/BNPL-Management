from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.errors import ConsentRequired
from app.modules.consent.application.ports import CifLinkRepository, ConsentRepository
from app.modules.consent.domain.entities import (
    CifLink,
    Consent,
    ConsentScope,
)


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ConsentService:
    """Grants, revokes, and enforces consent; maintains profile<->CIF links."""

    def __init__(
        self,
        consents: ConsentRepository,
        links: CifLinkRepository,
        now: Callable[[], datetime] = _utcnow,
    ) -> None:
        self._consents = consents
        self._links = links
        self._now = now

    def now(self) -> datetime:
        return self._now()

    async def grant(
        self,
        cif: str,
        scopes: Iterable[ConsentScope],
        granted_by: str,
        subject: str | None = None,
        ttl_days: int | None = None,
    ) -> Consent:
        now = self._now()
        expires_at = now + timedelta(days=ttl_days) if ttl_days else None
        consent = Consent(
            id=f"cons_{uuid4().hex}",
            cif=cif,
            scopes=tuple(dict.fromkeys(scopes)),
            granted_by=granted_by,
            granted_at=now,
            subject=subject,
            expires_at=expires_at,
        )
        await self._consents.add(consent)
        return consent

    async def get(self, consent_id: str) -> Consent:
        return await self._consents.get(consent_id)

    async def revoke(self, consent_id: str) -> Consent:
        consent = await self._consents.get(consent_id)
        if consent.revoked_at is not None:
            return consent
        revoked = replace(consent, revoked_at=self._now())
        await self._consents.update(revoked)
        return revoked

    async def list_for_cif(self, cif: str) -> list[Consent]:
        return await self._consents.list_for_cif(cif)

    async def active_consent(self, cif: str, scope: ConsentScope) -> Consent | None:
        now = self._now()
        for consent in await self._consents.list_for_cif(cif):
            if consent.is_active(now) and consent.covers(scope):
                return consent
        return None

    async def ensure(self, cif: str, scope: ConsentScope) -> Consent:
        consent = await self.active_consent(cif, scope)
        if consent is None:
            raise ConsentRequired(cif, scope.value)
        return consent

    async def link_cif(
        self,
        profile_id: str,
        cif: str,
        consent_id: str | None = None,
    ) -> CifLink:
        link = CifLink(
            profile_id=profile_id,
            cif=cif,
            linked_at=self._now(),
            consent_id=consent_id,
        )
        await self._links.add(link)
        return link

    async def cifs_for_profile(self, profile_id: str) -> list[str]:
        links = await self._links.list_for_profile(profile_id)
        return sorted({link.cif for link in links})

    async def profiles_for_cif(self, cif: str) -> list[str]:
        links = await self._links.list_for_cif(cif)
        return sorted({link.profile_id for link in links})
