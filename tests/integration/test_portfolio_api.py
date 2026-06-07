from __future__ import annotations

from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient

import app.dependencies as deps
from app.main import create_app
from app.modules.ingestion.application.ports import CifSummary, TransactionRow
from app.modules.ingestion.application.service import IngestionService


class _SummarySource:
    def load(self, path: str) -> list[CifSummary]:
        return [CifSummary("100", "2025-01", 10_000_000, 4_000_000, 1_000_000)]


class _TransactionSource:
    def load(self, path: str) -> list[TransactionRow]:
        return [
            TransactionRow("100", "tra gop thang", datetime(2025, 1, 5), -1_000_000,
                           "Debt payment"),
            TransactionRow("100", "tra gop thang", datetime(2025, 2, 5), -1_000_000,
                           "Debt payment"),
        ]


@pytest.fixture
async def client(monkeypatch):
    ingestion = IngestionService(
        _SummarySource(),
        "summary.csv",
        transaction_source=_TransactionSource(),
        transaction_csv_path="tx.csv",
    )
    monkeypatch.setattr(deps, "get_ingestion_service", lambda: ingestion)
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_portfolio_summary_api(client):
    r = await client.get("/portfolio/summary")

    assert r.status_code == 200
    assert r.json()["total_customers"] == 1
