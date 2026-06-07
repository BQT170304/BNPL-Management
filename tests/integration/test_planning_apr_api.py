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
        "expenses": [{"category": "living", "amount": 10_000_000, "classification": "FIXED"}],
        "debts": [],
        "assets": [{"type": "CASH", "value": 40_000_000, "liquidity": "HIGH"}],
        "goals": [],
    }


async def test_simulate_exposes_cost_breakdown(client):
    await client.post("/profiles", json=_profile_body("apr_sim"))
    r = await client.post("/planning/simulate", json={
        "profile_id": "apr_sim",
        "item_name": "Phone",
        "amount": 12_000_000,
        "horizon_months": 6,
        "apr": 36.0,
        "fee": 300_000,
    })
    assert r.status_code == 200
    by_id = {s["scenario_id"]: s for s in r.json()["scenarios"]}
    bnpl = by_id["bnpl_6m"]["cost"]
    assert bnpl["total_interest"] > 0
    assert bnpl["total_fee"] == 300_000
    assert bnpl["total_cost"] > 12_000_000
    assert bnpl["break_even_month"] is not None
    # pay-full carries no interest
    assert by_id["pay_full"]["cost"]["total_interest"] == 0


async def test_recommend_accepts_financing_terms(client):
    await client.post("/profiles", json=_profile_body("apr_rec"))
    r = await client.post("/planning/recommend", json={
        "profile_id": "apr_rec",
        "item_name": "Phone",
        "amount": 15_000_000,
        "horizon_months": 6,
        "apr": 60.0,
        "fee": 500_000,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["best_scenario_id"] != "bnpl_12m"
    # input snapshot captured the terms for audit
    audit = await client.get(f"/decisions/{body['decision_id']}")
    assert audit.json()["input_snapshot"]["apr"] == 60.0
