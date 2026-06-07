from __future__ import annotations

from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient

import app.dependencies as deps
from app.core.clock import FixedClock
from app.main import create_app
from app.modules.forecasting.application.services import ForecastService


@pytest.fixture
async def client():
    app = create_app()
    app.dependency_overrides[deps.get_forecast_service] = lambda: ForecastService(
        FixedClock(date(2026, 6, 6)),
        deps.get_obligation_repository(),
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _profile_body(pid: str = "forecast_profile") -> dict:
    return {
        "id": pid,
        "income": {"salary": 20_000_000},
        "risk": "MEDIUM",
        "emergency_fund": 5_000_000,
        "expenses": [
            {"category": "rent", "amount": 6_000_000, "classification": "FIXED"},
            {"category": "food", "amount": 4_000_000, "classification": "SEMI_FIXED"},
        ],
        "debts": [
            {
                "name": "loan",
                "monthly_payment": 2_000_000,
                "balance": 20_000_000,
                "apr": 12.0,
                "months_remaining": 10,
                "debt_type": "INSTALLMENT",
            },
        ],
        "assets": [{"type": "CASH", "value": 10_000_000, "liquidity": "HIGH"}],
        "goals": [],
    }


def _obligation_body() -> dict:
    return {
        "id": "forecast_obl_1",
        "type": "BNPL",
        "merchant": "Phone Store",
        "category": "electronics",
        "principal_amount": 15_000_000,
        "monthly_payment": 2_500_000,
        "due_day": 25,
        "start_date": "2026-07-01",
        "remaining_terms": 6,
    }


async def test_forecast_profile_includes_obligations(client):
    await client.post("/profiles", json=_profile_body())
    await client.post("/profiles/forecast_profile/obligations", json=_obligation_body())

    r = await client.get("/profiles/forecast_profile/forecast?months=2")

    assert r.status_code == 200
    body = r.json()
    assert body["profile_id"] == "forecast_profile"
    assert len(body["months"]) == 2
    assert body["months"][0]["obligation_payment"] == 2_500_000
    assert body["months"][0]["net_cashflow"] == 5_500_000
    assert body["months"][0]["ending_balance"] == 15_500_000


async def test_forecast_missing_profile_returns_404(client):
    r = await client.get("/profiles/no_profile/forecast")

    assert r.status_code == 404


async def test_forecast_rejects_invalid_months(client):
    await client.post("/profiles", json=_profile_body("forecast_invalid_months"))

    r = await client.get("/profiles/forecast_invalid_months/forecast?months=0")

    assert r.status_code == 422
