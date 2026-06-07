from __future__ import annotations

from collections import defaultdict
from typing import Protocol

from app.modules.consent.application.ports import CifLinkRepository
from app.modules.ingestion.application.service import IngestionService


class DailyHistoryProvider(Protocol):
    async def daily_net_for_profile(self, profile_id: str) -> list[tuple[str, int]]: ...


class DailyCashflowHistoryProvider:
    """Daily net cashflow history for a profile, from the transaction-level data
    of the CIF(s) it is linked to. Net = sum(AMOUNT) per day (income positive,
    expense/debt negative)."""

    def __init__(self, links: CifLinkRepository, ingestion: IngestionService) -> None:
        self._links = links
        self._ingestion = ingestion

    async def daily_net_for_profile(self, profile_id: str) -> list[tuple[str, int]]:
        links = await self._links.list_for_profile(profile_id)
        if not links:
            return []
        by_day: dict[str, int] = defaultdict(int)
        for link in links:
            for row in self._ingestion.transactions_for_cif(link.cif):
                day = row.transacted_at.date().isoformat()
                by_day[day] += int(row.amount)
        return sorted(by_day.items())
