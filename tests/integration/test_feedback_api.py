from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

import app.dependencies as deps
from app.main import create_app
from app.modules.feedback.application.services import FeedbackService
from app.modules.feedback.infrastructure.memory_repository import InMemoryOutcomeRepository


@pytest.fixture
async def client(monkeypatch):
    # Fresh outcome store per test, but share the real decision repository so
    # decisions created via /planning/recommend are visible to feedback.
    feedback = FeedbackService(InMemoryOutcomeRepository(), deps.get_decision_repository())
    monkeypatch.setattr(deps, "get_feedback_service", lambda: feedback)
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _profile_body(pid: str, salary: int = 20_000_000, cash: int = 40_000_000,
                  expense: int = 8_000_000) -> dict:
    return {
        "id": pid,
        "income": {"salary": salary},
        "risk": "MEDIUM",
        "emergency_fund": 5_000_000,
        "expenses": [{"category": "living", "amount": expense, "classification": "FIXED"}],
        "debts": [],
        "assets": [{"type": "CASH", "value": cash, "liquidity": "HIGH"}],
        "goals": [],
    }


async def _recommend(client, profile_id: str, amount: int) -> str:
    r = await client.post("/planning/recommend", json={
        "profile_id": profile_id, "item_name": "Phone", "amount": amount, "horizon_months": 6,
    })
    return r.json()["decision_id"]


async def test_record_outcome_links_decision(client):
    await client.post("/profiles", json=_profile_body("fb_p1"))
    decision_id = await _recommend(client, "fb_p1", 15_000_000)

    r = await client.post(f"/decisions/{decision_id}/outcomes", json={
        "outcome": "PAID_ON_TIME", "recorded_by": "rm_bob",
    })
    assert r.status_code == 201
    body = r.json()
    assert body["decision_id"] == decision_id
    assert body["profile_id"] == "fb_p1"
    assert body["outcome"] == "PAID_ON_TIME"


async def test_record_outcome_missing_decision_404(client):
    r = await client.post("/decisions/dec_missing/outcomes", json={
        "outcome": "LATE", "recorded_by": "rm",
    })
    assert r.status_code == 404


async def test_dataset_export_joins_decision_and_outcome(client):
    await client.post("/profiles", json=_profile_body("fb_ds"))
    decision_id = await _recommend(client, "fb_ds", 15_000_000)
    await client.post(f"/decisions/{decision_id}/outcomes", json={
        "outcome": "DEFAULT", "recorded_by": "rm",
    })

    r = await client.get("/feedback/dataset")
    assert r.status_code == 200
    rows = r.json()["rows"]
    row = next(row for row in rows if row["decision_id"] == decision_id)
    assert row["outcome"] == "DEFAULT"
    assert row["machine_approved"] is True
    assert row["profile_id"] == "fb_ds"


async def test_metrics_compute_false_approve_and_false_reject(client):
    # Two approved decisions: one good, one bad.
    await client.post("/profiles", json=_profile_body("fb_a"))
    good = await _recommend(client, "fb_a", 15_000_000)
    bad = await _recommend(client, "fb_a", 15_000_000)
    await client.post(f"/decisions/{good}/outcomes", json={
        "outcome": "PAID_ON_TIME", "recorded_by": "rm"})
    await client.post(f"/decisions/{bad}/outcomes", json={
        "outcome": "DEFAULT", "recorded_by": "rm"})

    # One rejected decision (all scenarios blocked) that would have been fine.
    await client.post("/profiles", json=_profile_body(
        "fb_poor", salary=5_000_000, cash=1_000_000, expense=4_000_000))
    rejected = await _recommend(client, "fb_poor", 30_000_000)
    await client.post(f"/decisions/{rejected}/outcomes", json={
        "outcome": "PAID_ON_TIME", "recorded_by": "rm"})

    r = await client.get("/feedback/metrics")
    body = r.json()
    assert body["total_outcomes"] == 3
    assert body["approval_outcome_rate"] == 0.5     # 1 good of 2 approved
    assert body["false_approve_rate"] == 0.5        # 1 bad of 2 approved
    assert body["false_reject_rate"] == 1.0         # 1 good of 1 rejected
    assert body["late_rate"] == 0.0
    assert body["counts"]["DEFAULT"] == 1
    assert body["counts"]["PAID_ON_TIME"] == 2
