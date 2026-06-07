from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

import app.dependencies as deps
from app.main import create_app
from app.modules.consent.application.services import ConsentService
from app.modules.consent.infrastructure.memory_repository import (
    InMemoryCifLinkRepository,
    InMemoryConsentRepository,
)


@pytest.fixture
async def client(monkeypatch):
    consent_svc = ConsentService(InMemoryConsentRepository(), InMemoryCifLinkRepository())
    monkeypatch.setattr(deps, "get_consent_service", lambda: consent_svc)
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_grant_get_and_revoke_consent(client):
    created = await client.post("/consents", json={
        "cif": "100",
        "scopes": ["CIF_SUMMARY", "CIF_TRANSACTIONS"],
        "granted_by": "rm_alice",
        "subject": "Nguyen Van A",
    })
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "GRANTED"
    assert body["granted_by"] == "rm_alice"
    assert set(body["scopes"]) == {"CIF_SUMMARY", "CIF_TRANSACTIONS"}
    consent_id = body["consent_id"]

    fetched = await client.get(f"/consents/{consent_id}")
    assert fetched.status_code == 200
    assert fetched.json()["cif"] == "100"

    revoked = await client.post(f"/consents/{consent_id}/revoke")
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "REVOKED"


async def test_get_missing_consent_404(client):
    r = await client.get("/consents/nope")
    assert r.status_code == 404


async def test_list_cif_consents(client):
    await client.post("/consents", json={
        "cif": "100", "scopes": ["CIF_SUMMARY"], "granted_by": "rm",
    })
    r = await client.get("/cifs/100/consents")
    assert r.status_code == 200
    assert len(r.json()["consents"]) == 1


async def test_profile_cifs_empty_by_default(client):
    r = await client.get("/profiles/unknown/cifs")
    assert r.status_code == 200
    assert r.json() == {"profile_id": "unknown", "cifs": []}


async def test_grant_requires_scopes(client):
    r = await client.post("/consents", json={
        "cif": "100", "scopes": [], "granted_by": "rm",
    })
    assert r.status_code == 422
