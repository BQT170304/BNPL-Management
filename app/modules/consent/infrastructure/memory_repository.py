from __future__ import annotations

from app.core.errors import ConsentNotFound
from app.modules.consent.domain.entities import CifLink, Consent


class InMemoryConsentRepository:
    def __init__(self) -> None:
        self._store: dict[str, Consent] = {}

    async def add(self, consent: Consent) -> None:
        self._store[consent.id] = consent

    async def get(self, consent_id: str) -> Consent:
        if consent_id not in self._store:
            raise ConsentNotFound(consent_id)
        return self._store[consent_id]

    async def update(self, consent: Consent) -> None:
        if consent.id not in self._store:
            raise ConsentNotFound(consent.id)
        self._store[consent.id] = consent

    async def list_for_cif(self, cif: str) -> list[Consent]:
        return [c for c in self._store.values() if c.cif == cif]

    async def list_all(self) -> list[Consent]:
        return list(self._store.values())


class InMemoryCifLinkRepository:
    def __init__(self) -> None:
        self._links: list[CifLink] = []

    async def add(self, link: CifLink) -> None:
        for existing in self._links:
            if existing.profile_id == link.profile_id and existing.cif == link.cif:
                return
        self._links.append(link)

    async def list_for_profile(self, profile_id: str) -> list[CifLink]:
        return [link for link in self._links if link.profile_id == profile_id]

    async def list_for_cif(self, cif: str) -> list[CifLink]:
        return [link for link in self._links if link.cif == cif]
