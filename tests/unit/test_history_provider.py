from __future__ import annotations

from datetime import UTC, datetime

from app.modules.consent.domain.entities import CifLink
from app.modules.consent.infrastructure.memory_repository import InMemoryCifLinkRepository
from app.modules.forecasting.application.history_provider import CifCashflowHistoryProvider
from app.modules.ingestion.application.ports import CifSummary

NOW = datetime(2026, 6, 1, tzinfo=UTC)


class _FakeIngestion:
    def __init__(self, rows: list[CifSummary]) -> None:
        self._rows = rows

    def summaries_for_cif(self, cif: str) -> list[CifSummary]:
        return [row for row in self._rows if row.cif == cif]


async def test_history_aggregates_net_cashflow_by_month():
    rows = [
        CifSummary("100", "2025-01", 10_000_000, 4_000_000, 1_000_000),  # net 5,000,000
        CifSummary("100", "2025-02", 12_000_000, 5_000_000, 2_000_000),  # net 5,000,000
    ]
    links = InMemoryCifLinkRepository()
    await links.add(CifLink(profile_id="p1", cif="100", linked_at=NOW))
    provider = CifCashflowHistoryProvider(links, _FakeIngestion(rows))

    history = await provider.history_for_profile("p1")
    assert [(p.month, p.net_cashflow) for p in history] == [
        ("2025-01", 5_000_000),
        ("2025-02", 5_000_000),
    ]


async def test_history_empty_when_no_links():
    provider = CifCashflowHistoryProvider(InMemoryCifLinkRepository(), _FakeIngestion([]))
    assert await provider.history_for_profile("nobody") == []
