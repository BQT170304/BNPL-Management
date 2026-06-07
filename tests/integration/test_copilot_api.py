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


async def test_purchase_question_invokes_real_simulator(client):
    await client.post("/profiles", json=_profile_body("cop_p1"))
    r = await client.post("/copilot/chat", json={
        "profile_id": "cop_p1",
        "message": "Tôi có nên mua điện thoại 15 triệu trả góp 6 tháng không?",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["tool"] == "RECOMMEND"
    assert body["used_optimizer"] is True
    assert body["decision_id"].startswith("dec_")

    # the copilot answers from the audit trace via explain
    explain = await client.post("/copilot/chat", json={
        "decision_id": body["decision_id"],
        "message": "Giải thích quyết định này tại sao",
    })
    assert explain.status_code == 200
    ebody = explain.json()
    assert ebody["tool"] == "EXPLAIN"
    assert ebody["decision_id"] == body["decision_id"]
    assert ebody["reply"]


async def test_copilot_does_not_self_approve_without_profile(client):
    r = await client.post("/copilot/chat", json={
        "message": "Tôi có nên mua điện thoại 15 triệu không?",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["tool"] == "CLARIFY"
    assert body["used_optimizer"] is False
    assert body["decision_id"] is None


async def test_copilot_forecast_and_alerts(client):
    await client.post("/profiles", json=_profile_body("cop_fc"))
    forecast = await client.post("/copilot/chat", json={
        "profile_id": "cop_fc", "message": "Cho mình xem dự báo dòng tiền",
    })
    assert forecast.json()["tool"] == "FORECAST"
    assert "next_30_net" in forecast.json()["data"]

    alerts = await client.post("/copilot/chat", json={
        "profile_id": "cop_fc", "message": "Có cảnh báo rủi ro gì không?",
    })
    assert alerts.json()["tool"] == "ALERTS"
