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


def _negative_profile(pid: str) -> dict:
    return {
        "id": pid,
        "income": {"salary": 10_000_000},
        "risk": "MEDIUM",
        "emergency_fund": 2_000_000,
        "expenses": [{"category": "rent", "amount": 13_000_000, "classification": "FIXED"}],
        "debts": [],
        "assets": [],
        "goals": [],
    }


async def test_alerts_without_forecast_have_no_projected_codes(client):
    await client.post("/profiles", json=_negative_profile("alert_base"))
    r = await client.get("/profiles/alert_base/alerts")
    assert r.status_code == 200
    codes = {a["code"] for a in r.json()["alerts"]}
    assert not any(code.startswith("PROJECTED_") for code in codes)


async def test_alerts_with_forecast_include_projected_negative_balance(client):
    await client.post("/profiles", json=_negative_profile("alert_fc"))
    r = await client.get("/profiles/alert_fc/alerts?include_forecast=true")
    assert r.status_code == 200
    alerts = r.json()["alerts"]
    projected = [a for a in alerts if a["code"] == "PROJECTED_NEGATIVE_BALANCE"]
    assert projected, alerts
    assert projected[0]["month"] is not None
    assert projected[0]["level"] == "CRITICAL"


async def test_forecast_endpoint_returns_summary(client):
    await client.post("/profiles", json=_negative_profile("fc_summary"))
    r = await client.get("/profiles/fc_summary/forecast?months=6")
    assert r.status_code == 200
    summary = r.json()["summary"]
    assert set(summary) == {"next_30_net", "next_90_net", "min_projected_balance"}
    assert summary["min_projected_balance"] < 0
