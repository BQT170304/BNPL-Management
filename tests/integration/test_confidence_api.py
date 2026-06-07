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


def _low_conf_obligation_body() -> dict:
    return {
        "id": "conf_auto_1",
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


async def test_decision_audit_contains_confidence(client):
    await client.post("/profiles", json=_profile_body("conf_profile"))
    await client.post("/profiles/conf_profile/obligations", json=_low_conf_obligation_body())

    r = await client.post("/planning/recommend", json={
        "profile_id": "conf_profile",
        "item_name": "Phone",
        "amount": 9_000_000,
        "horizon_months": 6,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["min_confidence"] == 0.4
    assert "LOW_CONFIDENCE_OBLIGATION" in body["advisories"]
    assert "VERIFY_OBLIGATION_BEFORE_DECISION" in body["advisories"]
    assert "tra gop dien may" in body["low_confidence_obligations"]

    # audit trace preserves confidence (no conflation of certain vs parsed data)
    audit = await client.get(f"/decisions/{body['decision_id']}")
    rec = audit.json()["recommendation"]
    assert rec["min_confidence"] == 0.4
    assert "LOW_CONFIDENCE_OBLIGATION" in rec["advisories"]

    # XAI explains the reduced confidence and tells the user to verify
    explanation = await client.post(f"/decisions/{body['decision_id']}/explain")
    reasons = " ".join(explanation.json()["key_reasons"])
    assert "xác minh" in reasons.lower()
    assert "tra gop dien may" in reasons
