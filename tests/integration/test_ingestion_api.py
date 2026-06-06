import pytest
from httpx import ASGITransport, AsyncClient

import app.dependencies as deps
from app.main import create_app
from app.modules.ingestion.application.ports import CifSummary
from app.modules.ingestion.application.service import IngestionService


class _StubSource:
    def load(self, path: str) -> list[CifSummary]:
        return [
            CifSummary("100", "2025-01", 10_000_000, 4_000_000, 1_000_000),
            CifSummary("100", "2025-02", 12_000_000, 5_000_000, 2_000_000),
        ]


@pytest.fixture
async def client(monkeypatch):
    svc = IngestionService(_StubSource(), csv_path="x.csv")
    monkeypatch.setattr(deps, "get_ingestion_service", lambda: svc)
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test",
        headers={"Authorization": "Bearer demo-token-bnpl"},
    ) as c:
        yield c


async def test_list_cifs(client):
    r = await client.get("/ingestion/cifs")
    assert r.status_code == 200
    assert r.json() == {"cifs": ["100"]}


async def test_get_seed_latest(client):
    r = await client.get("/ingestion/cif/100/seed?strategy=latest")
    assert r.status_code == 200
    assert r.json() == {"cif": "100", "income": 12_000_000,
                        "expense": 5_000_000, "debt_payment": 2_000_000}


async def test_get_seed_unknown_cif_404(client):
    r = await client.get("/ingestion/cif/999/seed")
    assert r.status_code == 404
