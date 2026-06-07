from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture
async def client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _profile_body(pid: str = "obl_profile") -> dict:
    return {
        "id": pid,
        "income": {"salary": 20_000_000},
        "risk": "MEDIUM",
        "emergency_fund": 30_000_000,
        "expenses": [],
        "debts": [],
        "assets": [],
        "goals": [],
    }


def _obligation_body(oid: str = "obl_1") -> dict:
    return {
        "id": oid,
        "type": "BNPL",
        "merchant": "Phone Store",
        "category": "electronics",
        "principal_amount": 15_000_000,
        "monthly_payment": 2_500_000,
        "due_day": 25,
        "start_date": "2026-07-01",
        "end_date": "2026-12-01",
        "remaining_terms": 6,
        "apr": 0.0,
        "status": "ACTIVE",
    }


async def test_create_list_and_delete_obligation(client):
    await client.post("/profiles", json=_profile_body())

    created = await client.post(
        "/profiles/obl_profile/obligations",
        json=_obligation_body(),
    )
    assert created.status_code == 201
    assert created.json()["monthly_payment"] == 2_500_000

    listed = await client.get("/profiles/obl_profile/obligations")
    assert listed.status_code == 200
    assert [o["id"] for o in listed.json()["obligations"]] == ["obl_1"]

    deleted = await client.delete("/profiles/obl_profile/obligations/obl_1")
    assert deleted.status_code == 204

    listed_after_delete = await client.get("/profiles/obl_profile/obligations")
    assert listed_after_delete.json() == {"obligations": []}


async def test_create_obligation_missing_profile_returns_404(client):
    r = await client.post("/profiles/missing/obligations", json=_obligation_body("missing_profile"))
    assert r.status_code == 404


async def test_delete_missing_obligation_returns_404(client):
    await client.post("/profiles", json=_profile_body("delete_missing_profile"))

    r = await client.delete("/profiles/delete_missing_profile/obligations/nope")

    assert r.status_code == 404


async def test_create_obligation_rejects_invalid_due_day(client):
    await client.post("/profiles", json=_profile_body("invalid_obligation_profile"))
    body = _obligation_body("invalid_due_day")
    body["due_day"] = 32

    r = await client.post("/profiles/invalid_obligation_profile/obligations", json=body)

    assert r.status_code == 422
