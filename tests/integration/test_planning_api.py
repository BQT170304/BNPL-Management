from __future__ import annotations

from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient

import app.dependencies as deps
from app.core.clock import FixedClock
from app.main import create_app
from app.modules.forecasting.application.services import ForecastService
from app.modules.planning.application.simulator import ScenarioSimulator


@pytest.fixture
async def client():
    app = create_app()

    def simulator() -> ScenarioSimulator:
        clock = FixedClock(date(2026, 6, 6))
        return ScenarioSimulator(
            clock,
            ForecastService(clock, deps.get_obligation_repository()),
        )

    app.dependency_overrides[deps.get_scenario_simulator] = simulator
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _profile_body(pid: str = "planning_profile") -> dict:
    return {
        "id": pid,
        "income": {"salary": 20_000_000},
        "risk": "MEDIUM",
        "emergency_fund": 5_000_000,
        "expenses": [
            {"category": "rent", "amount": 6_000_000, "classification": "FIXED"},
            {"category": "food", "amount": 4_000_000, "classification": "SEMI_FIXED"},
        ],
        "debts": [],
        "assets": [{"type": "CASH", "value": 20_000_000, "liquidity": "HIGH"}],
        "goals": [],
    }


async def test_simulate_purchase_returns_scenarios(client):
    await client.post("/profiles", json=_profile_body())

    r = await client.post("/planning/simulate", json={
        "profile_id": "planning_profile",
        "item_name": "Phone",
        "amount": 15_000_000,
        "horizon_months": 2,
    })

    assert r.status_code == 200
    body = r.json()
    assert body["profile_id"] == "planning_profile"
    assert len(body["scenarios"]) == 6
    by_id = {scenario["scenario_id"]: scenario for scenario in body["scenarios"]}
    assert by_id["bnpl_6m"]["monthly_payment"] == 2_500_000
    assert by_id["delay_1m_bnpl_6m"]["forecast"][0]["obligation_payment"] == 0
    assert by_id["delay_1m_bnpl_6m"]["forecast"][1]["obligation_payment"] == 2_500_000


async def test_simulate_missing_profile_returns_404(client):
    r = await client.post("/planning/simulate", json={
        "profile_id": "no_profile",
        "item_name": "Phone",
        "amount": 15_000_000,
    })

    assert r.status_code == 404


async def test_simulate_rejects_invalid_amount(client):
    await client.post("/profiles", json=_profile_body("planning_invalid_amount"))

    r = await client.post("/planning/simulate", json={
        "profile_id": "planning_invalid_amount",
        "item_name": "Phone",
        "amount": 0,
    })

    assert r.status_code == 422
