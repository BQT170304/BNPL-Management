from __future__ import annotations

from typing import Protocol

from app.modules.consent.application.ports import CifLinkRepository
from app.modules.forecasting.domain.history import MonthlyCashflowPoint
from app.modules.ingestion.application.service import IngestionService


class CashflowHistoryProvider(Protocol):
    async def history_for_profile(self, profile_id: str) -> list[MonthlyCashflowPoint]: ...


class CifCashflowHistoryProvider:
    """Builds a monthly base-cashflow history for a profile from the monthly
    summaries of the CIF(s) it is linked to (Phase 8 mapping)."""

    def __init__(self, links: CifLinkRepository, ingestion: IngestionService) -> None:
        self._links = links
        self._ingestion = ingestion

    async def history_for_profile(self, profile_id: str) -> list[MonthlyCashflowPoint]:
        links = await self._links.list_for_profile(profile_id)
        if not links:
            return []
        by_month: dict[str, int] = {}
        for link in links:
            for summary in self._ingestion.summaries_for_cif(link.cif):
                net = summary.income - summary.expense - summary.debt_payment
                by_month[summary.month] = by_month.get(summary.month, 0) + net
        return [
            MonthlyCashflowPoint(month=month, net_cashflow=net)
            for month, net in sorted(by_month.items())
        ]
