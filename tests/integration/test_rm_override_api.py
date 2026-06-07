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


def _profile_body(pid: str) -> dict:
    return {
        "id": pid,
        "income": {"salary": 20_000_000},
        "risk": "MEDIUM",
        "emergency_fund": 5_000_000,
        "expenses": [{"category": "living", "amount": 8_000_000, "classification": "FIXED"}],
        "debts": [],
        "assets": [{"type": "CASH", "value": 40_000_000, "liquidity": "HIGH"}],
        "goals": [],
    }


def _obligation_body() -> dict:
    return {
        "id": "verify_ob_1",
        "type": "LOAN",
        "merchant": "tra gop dien may",
        "category": "debt",
        "principal_amount": 6_000_000,
        "monthly_payment": 500_000,
        "due_day": 10,
        "start_date": "2026-01-01",
        "end_date": None,
        "remaining_terms": 24,
        "apr": 0.0,
        "status": "ACTIVE",
        "confidence": 0.4,
    }


async def test_verify_obligation(client):
    await client.post("/profiles", json=_profile_body("verify_profile"))
    await client.post("/profiles/verify_profile/obligations", json=_obligation_body())

    r = await client.post("/obligations/verify_ob_1/verify", json={"verified_by": "rm_bob"})
    assert r.status_code == 200
    body = r.json()
    assert body["confidence"] == 1.0
    assert body["verified"] is True
    assert body["verified_by"] == "rm_bob"

    listed = await client.get("/profiles/verify_profile/obligations")
    assert listed.json()["obligations"][0]["verified"] is True


async def test_verify_missing_obligation_404(client):
    r = await client.post("/obligations/nope/verify", json={"verified_by": "rm"})
    assert r.status_code == 404


async def test_override_records_human_decision_with_audit(client):
    await client.post("/profiles", json=_profile_body("override_profile"))
    rec = await client.post("/planning/recommend", json={
        "profile_id": "override_profile",
        "item_name": "Phone",
        "amount": 15_000_000,
        "horizon_months": 6,
    })
    decision_id = rec.json()["decision_id"]
    machine_best = rec.json()["best_scenario_id"]

    r = await client.post(f"/decisions/{decision_id}/override", json={
        "actor": "rm_alice",
        "action": "REJECT",
        "reason": "Khách sắp mất việc, hoãn cấp tín dụng.",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["override"]["actor"] == "rm_alice"
    assert body["override"]["action"] == "REJECT"
    assert body["override"]["reason"]
    assert body["override"]["created_at"]
    # machine decision is preserved, not overwritten
    assert body["recommendation"]["best_scenario_id"] == machine_best

    audit = await client.get(f"/decisions/{decision_id}")
    assert audit.json()["override"]["actor"] == "rm_alice"
    assert audit.json()["recommendation"]["best_scenario_id"] == machine_best


async def test_override_requires_reason(client):
    await client.post("/profiles", json=_profile_body("override_noreason"))
    rec = await client.post("/planning/recommend", json={
        "profile_id": "override_noreason",
        "item_name": "Phone",
        "amount": 15_000_000,
    })
    decision_id = rec.json()["decision_id"]

    r = await client.post(f"/decisions/{decision_id}/override", json={
        "actor": "rm_alice",
        "action": "REJECT",
        "reason": "",
    })
    assert r.status_code == 422


async def test_override_missing_decision_404(client):
    r = await client.post("/decisions/dec_missing/override", json={
        "actor": "rm", "action": "APPROVE", "reason": "ok",
    })
    assert r.status_code == 404
