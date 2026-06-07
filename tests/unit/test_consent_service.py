from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.core.errors import ConsentRequired
from app.modules.consent.application.services import ConsentService
from app.modules.consent.domain.entities import ConsentScope
from app.modules.consent.infrastructure.memory_repository import (
    InMemoryCifLinkRepository,
    InMemoryConsentRepository,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _service(now=NOW) -> ConsentService:
    return ConsentService(
        InMemoryConsentRepository(),
        InMemoryCifLinkRepository(),
        now=lambda: now,
    )


async def test_grant_and_ensure_active_consent():
    service = _service()
    consent = await service.grant("100", [ConsentScope.CIF_SUMMARY], granted_by="rm")
    assert consent.granted_by == "rm"
    ensured = await service.ensure("100", ConsentScope.CIF_SUMMARY)
    assert ensured.id == consent.id


async def test_ensure_without_consent_raises():
    service = _service()
    with pytest.raises(ConsentRequired):
        await service.ensure("100", ConsentScope.CIF_SUMMARY)


async def test_ensure_wrong_scope_raises():
    service = _service()
    await service.grant("100", [ConsentScope.CIF_SUMMARY], granted_by="rm")
    with pytest.raises(ConsentRequired):
        await service.ensure("100", ConsentScope.CIF_TRANSACTIONS)


async def test_revoked_consent_no_longer_satisfies_ensure():
    service = _service()
    consent = await service.grant("100", [ConsentScope.CIF_SUMMARY], granted_by="rm")
    await service.revoke(consent.id)
    with pytest.raises(ConsentRequired):
        await service.ensure("100", ConsentScope.CIF_SUMMARY)


async def test_expired_consent_not_returned():
    repo = InMemoryConsentRepository()
    links = InMemoryCifLinkRepository()
    grant_service = ConsentService(repo, links, now=lambda: NOW)
    await grant_service.grant("100", [ConsentScope.CIF_SUMMARY], granted_by="rm", ttl_days=1)

    later_service = ConsentService(repo, links, now=lambda: NOW + timedelta(days=2))
    with pytest.raises(ConsentRequired):
        await later_service.ensure("100", ConsentScope.CIF_SUMMARY)


async def test_scopes_are_deduped():
    service = _service()
    consent = await service.grant(
        "100",
        [ConsentScope.CIF_SUMMARY, ConsentScope.CIF_SUMMARY],
        granted_by="rm",
    )
    assert consent.scopes == (ConsentScope.CIF_SUMMARY,)


async def test_cif_mapping_is_many_to_many():
    service = _service()
    await service.link_cif("profile_a", "100")
    await service.link_cif("profile_a", "200")
    await service.link_cif("profile_b", "100")
    assert await service.cifs_for_profile("profile_a") == ["100", "200"]
    assert await service.profiles_for_cif("100") == ["profile_a", "profile_b"]


async def test_link_cif_is_idempotent():
    service = _service()
    await service.link_cif("profile_a", "100")
    await service.link_cif("profile_a", "100")
    assert await service.cifs_for_profile("profile_a") == ["100"]
