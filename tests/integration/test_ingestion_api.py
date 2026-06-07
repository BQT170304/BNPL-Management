import pytest
from httpx import ASGITransport, AsyncClient

import app.dependencies as deps
from app.main import create_app
from app.modules.consent.application.services import ConsentService
from app.modules.consent.infrastructure.memory_repository import (
    InMemoryCifLinkRepository,
    InMemoryConsentRepository,
)
from app.modules.ingestion.application.ports import CifSummary, TransactionRow
from app.modules.ingestion.application.service import IngestionService
from app.modules.obligations.infrastructure.memory_repository import InMemoryObligationRepository


class _StubSource:
    def load(self, path: str) -> list[CifSummary]:
        return [
            CifSummary("100", "2025-01", 10_000_000, 4_000_000, 1_000_000),
            CifSummary("100", "2025-02", 12_000_000, 5_000_000, 2_000_000),
        ]


class _StubTransactionSource:
    def load(self, path: str) -> list[TransactionRow]:
        from datetime import datetime

        return [
            TransactionRow("100", "tra gop thang", datetime(2025, 1, 5), -1_200_000,
                           "Debt payment"),
            TransactionRow("100", "tra gop thang", datetime(2025, 2, 5), -1_800_000,
                           "Debt payment"),
        ]


@pytest.fixture
async def client(monkeypatch):
    svc = IngestionService(
        _StubSource(),
        csv_path="x.csv",
        transaction_source=_StubTransactionSource(),
        transaction_csv_path="tx.csv",
    )
    obligation_repo = InMemoryObligationRepository()
    consent_svc = ConsentService(InMemoryConsentRepository(), InMemoryCifLinkRepository())
    monkeypatch.setattr(deps, "get_ingestion_service", lambda: svc)
    monkeypatch.setattr(deps, "get_obligation_repository", lambda: obligation_repo)
    monkeypatch.setattr(deps, "get_consent_service", lambda: consent_svc)
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test",
        headers={"Authorization": "Bearer demo-token-bnpl"},
    ) as c:
        yield c


async def _grant(client, cif: str, scopes: list[str]) -> None:
    r = await client.post("/consents", json={
        "cif": cif,
        "scopes": scopes,
        "granted_by": "tester",
    })
    assert r.status_code == 201


async def test_list_cifs(client):
    r = await client.get("/ingestion/cifs")
    assert r.status_code == 200
    assert r.json() == {"cifs": ["100"]}


async def test_get_seed_without_consent_is_forbidden(client):
    r = await client.get("/ingestion/cif/100/seed?strategy=latest")
    assert r.status_code == 403
    assert r.json()["code"] == "CONSENT_REQUIRED"


async def test_get_seed_latest(client):
    await _grant(client, "100", ["CIF_SUMMARY"])
    r = await client.get("/ingestion/cif/100/seed?strategy=latest")
    assert r.status_code == 200
    assert r.json() == {"cif": "100", "income": 12_000_000,
                        "expense": 5_000_000, "debt_payment": 2_000_000}


async def test_get_seed_unknown_cif_404(client):
    await _grant(client, "999", ["CIF_SUMMARY"])
    r = await client.get("/ingestion/cif/999/seed")
    assert r.status_code == 404


async def test_get_obligation_seeds_without_consent_is_forbidden(client):
    r = await client.get("/ingestion/cif/100/obligation-seeds")
    assert r.status_code == 403


async def test_get_obligation_seeds(client):
    await _grant(client, "100", ["CIF_TRANSACTIONS"])
    r = await client.get("/ingestion/cif/100/obligation-seeds")

    assert r.status_code == 200
    body = r.json()
    assert body["cif"] == "100"
    assert body["obligations"][0]["type"] == "BNPL"
    assert body["obligations"][0]["monthly_payment"] == 1_500_000


async def test_seed_obligations_without_consent_is_forbidden(client):
    await client.post("/profiles", json={
        "id": "profile_no_consent",
        "income": {"salary": 12_000_000},
        "risk": "MEDIUM",
        "expenses": [],
        "debts": [],
        "assets": [],
        "goals": [],
    })

    r = await client.post("/profiles/profile_no_consent/obligations/from-cif/100")
    assert r.status_code == 403


async def test_seed_obligations_from_cif(client):
    await client.post("/profiles", json={
        "id": "profile_seed",
        "income": {"salary": 12_000_000},
        "risk": "MEDIUM",
        "expenses": [],
        "debts": [],
        "assets": [],
        "goals": [],
    })
    await _grant(client, "100", ["CIF_TRANSACTIONS"])

    r = await client.post("/profiles/profile_seed/obligations/from-cif/100")

    assert r.status_code == 200
    body = r.json()
    assert body["profile_id"] == "profile_seed"
    assert body["obligations"][0]["id"] == "profile_seed_auto_tra_gop_thang"

    listed = await client.get("/profiles/profile_seed/obligations")
    assert listed.json()["obligations"][0]["monthly_payment"] == 1_500_000

    # CIF is now mapped to the profile.
    mapping = await client.get("/profiles/profile_seed/cifs")
    assert mapping.json() == {"profile_id": "profile_seed", "cifs": ["100"]}
