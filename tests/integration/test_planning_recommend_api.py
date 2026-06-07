from __future__ import annotations

from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient

import app.dependencies as deps
from app.core.clock import FixedClock
from app.main import create_app
from app.modules.forecasting.application.services import ForecastService
from app.modules.planning.application.optimizer import ConstraintOptimizer
from app.modules.planning.application.simulator import ScenarioSimulator


@pytest.fixture
async def client():
    app = create_app()

    def optimizer() -> ConstraintOptimizer:
        clock = FixedClock(date(2026, 6, 6))
        simulator = ScenarioSimulator(
            clock,
            ForecastService(clock, deps.get_obligation_repository()),
        )
        return ConstraintOptimizer(simulator)

    app.dependency_overrides[deps.get_constraint_optimizer] = optimizer
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _profile_body(pid: str = "recommend_profile") -> dict:
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


async def test_recommend_purchase_returns_best_scenario(client):
    await client.post("/profiles", json=_profile_body())

    r = await client.post("/planning/recommend", json={
        "profile_id": "recommend_profile",
        "item_name": "Phone",
        "amount": 15_000_000,
        "horizon_months": 6,
    })

    assert r.status_code == 200
    body = r.json()
    assert body["decision_id"].startswith("dec_")
    assert body["best_scenario_id"] == "bnpl_12m"
    by_id = {decision["scenario"]["scenario_id"]: decision for decision in body["scenarios"]}
    assert by_id["bnpl_12m"]["recommended"] is True
    assert by_id["pay_full"]["blocked"] is True
    assert "EFR_BELOW_LIMIT" in by_id["pay_full"]["reason_codes"]
    assert (
        by_id["bnpl_12m"]["score_breakdown"]["weighted_total"]
        == by_id["bnpl_12m"]["score"]
    )

    audit = await client.get(f"/decisions/{body['decision_id']}")
    assert audit.status_code == 200
    audit_body = audit.json()
    assert audit_body["decision_id"] == body["decision_id"]
    assert audit_body["input_snapshot"]["profile_id"] == "recommend_profile"
    assert audit_body["recommendation"]["best_scenario_id"] == "bnpl_12m"

    explanation = await client.post(f"/decisions/{body['decision_id']}/explain")
    assert explanation.status_code == 200
    assert explanation.json()["decision_id"] == body["decision_id"]
    assert explanation.json()["key_reasons"]


async def test_recommend_missing_profile_returns_404(client):
    r = await client.post("/planning/recommend", json={
        "profile_id": "no_profile",
        "item_name": "Phone",
        "amount": 15_000_000,
    })

    assert r.status_code == 404


async def test_get_missing_decision_returns_404(client):
    r = await client.get("/decisions/dec_missing")

    assert r.status_code == 404


async def test_quick_simulate_does_not_record_decision(client):
    await client.post("/profiles", json=_profile_body("quicksim_profile"))
    r = await client.post("/planning/recommend", json={
        "profile_id": "quicksim_profile",
        "item_name": "Phone",
        "amount": 15_000_000,
        "horizon_months": 6,
        "record": False,
    })
    assert r.status_code == 200
    body = r.json()
    # full scored result is returned (optimizer ran)...
    assert body["best_scenario_id"] is not None
    assert body["scenarios"]
    # ...but no decision was persisted
    assert body["decision_id"] is None


async def test_recommend_records_by_default(client):
    await client.post("/profiles", json=_profile_body("rec_default_profile"))
    r = await client.post("/planning/recommend", json={
        "profile_id": "rec_default_profile", "item_name": "Phone", "amount": 15_000_000,
    })
    assert r.json()["decision_id"].startswith("dec_")
