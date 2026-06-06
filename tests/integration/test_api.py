import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture
async def client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test",
        headers={"Authorization": "Bearer demo-token-bnpl"},
    ) as c:
        yield c


def _profile_body() -> dict:
    return {
        "id": "p1",
        "income": {"salary": 10_000_000, "secondary": 3_000_000,
                   "avg_bonus_monthly": 1_000_000, "passive": 500_000},
        "risk": "MEDIUM", "emergency_fund": 20_000_000,
        "expenses": [
            {"category": "rent", "amount": 3_000_000, "classification": "FIXED"},
            {"category": "food", "amount": 3_000_000, "classification": "SEMI_FIXED"},
            {"category": "transport", "amount": 500_000, "classification": "SEMI_FIXED"},
            {"category": "internet", "amount": 300_000, "classification": "FIXED"},
            {"category": "fun", "amount": 1_000_000, "classification": "DISCRETIONARY"},
        ],
        "debts": [
            {"name": "cc", "monthly_payment": 2_000_000, "balance": None,
             "apr": 30.0, "months_remaining": None, "debt_type": "REVOLVING"},
            {"name": "bnpl", "monthly_payment": 1_500_000, "balance": 9_000_000,
             "apr": 0.0, "months_remaining": 6, "debt_type": "INSTALLMENT"},
            {"name": "car", "monthly_payment": 2_000_000, "balance": 100_000_000,
             "apr": 10.0, "months_remaining": 50, "debt_type": "SECURED"},
        ],
        "assets": [{"type": "CASH", "value": 20_000_000, "liquidity": "HIGH"}],
        "goals": [
            {"id": "car", "name": "Car", "target_amount": 300_000_000,
             "deadline": "2027-12-01", "priority": "HIGH", "savings_allocated": 0},
        ],
    }


async def test_create_and_analyze_profile(client):
    r = await client.post("/profiles", json=_profile_body())
    assert r.status_code == 201

    a = await client.get("/profiles/p1/analysis")
    assert a.status_code == 200
    body = a.json()
    assert body["ncf"] == 1_200_000
    assert round(body["dti"], 2) == 37.93
    assert body["dti_band"] == "WARNING"


async def test_analyze_missing_profile_returns_404(client):
    r = await client.get("/profiles/ghost/analysis")
    assert r.status_code == 404


async def test_evaluate_purchase(client):
    await client.post("/profiles", json=_profile_body())
    r = await client.post("/advisory/evaluate", json={
        "profile_id": "p1", "item_name": "Phone", "purchase_amount": 15_000_000,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["scorer_used"] == "deterministic"
    assert len(body["options"]) == 4
    assert "best_option_id" in body
