from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.modules.consent.domain.entities import (
    CifLink,
    Consent,
    ConsentScope,
    ConsentStatus,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _consent(**kwargs) -> Consent:
    base = dict(
        id="cons_1",
        cif="100",
        scopes=(ConsentScope.CIF_SUMMARY,),
        granted_by="user",
        granted_at=NOW,
    )
    base.update(kwargs)
    return Consent(**base)


def test_active_consent_is_granted():
    consent = _consent()
    assert consent.status_at(NOW) == ConsentStatus.GRANTED
    assert consent.is_active(NOW)


def test_revoked_consent_is_not_active():
    consent = _consent(revoked_at=NOW + timedelta(hours=1))
    assert consent.status_at(NOW + timedelta(hours=2)) == ConsentStatus.REVOKED
    assert not consent.is_active(NOW + timedelta(hours=2))


def test_expired_consent_is_not_active():
    consent = _consent(expires_at=NOW + timedelta(days=1))
    assert consent.is_active(NOW)
    assert consent.status_at(NOW + timedelta(days=2)) == ConsentStatus.EXPIRED
    assert not consent.is_active(NOW + timedelta(days=2))


def test_covers_scope():
    consent = _consent(scopes=(ConsentScope.CIF_SUMMARY, ConsentScope.CIF_TRANSACTIONS))
    assert consent.covers(ConsentScope.CIF_TRANSACTIONS)
    assert _consent().covers(ConsentScope.CIF_SUMMARY)
    assert not _consent().covers(ConsentScope.CIF_TRANSACTIONS)


def test_consent_requires_scopes():
    with pytest.raises(ValueError):
        _consent(scopes=())


def test_consent_requires_granted_by():
    with pytest.raises(ValueError):
        _consent(granted_by="")


def test_expiry_must_be_after_grant():
    with pytest.raises(ValueError):
        _consent(expires_at=NOW)


def test_cif_link_requires_ids():
    with pytest.raises(ValueError):
        CifLink(profile_id="", cif="100", linked_at=NOW)
    with pytest.raises(ValueError):
        CifLink(profile_id="p1", cif="", linked_at=NOW)
