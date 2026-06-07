from __future__ import annotations

from datetime import date

import pytest

from app.core.clock import FixedClock
from app.modules.forecasting.application.cashflow_forecaster import ProphetCashflowForecaster
from app.modules.forecasting.application.services import ForecastService
from app.modules.forecasting.domain.history import MonthlyCashflowPoint
from app.modules.obligations.infrastructure.memory_repository import InMemoryObligationRepository
from app.modules.profiles.domain.entities import Expense, FinancialProfile, Income
from app.modules.profiles.domain.value_objects import ExpenseClass, RiskTolerance


class _FakeProvider:
    def __init__(self, points: list[MonthlyCashflowPoint]) -> None:
        self._points = points

    async def history_for_profile(self, profile_id: str) -> list[MonthlyCashflowPoint]:
        return self._points


def _profile() -> FinancialProfile:
    # current base = 20M - 8M = 12M (flat engine would use this every month)
    return FinancialProfile(
        id="p1",
        income=Income(20_000_000),
        risk=RiskTolerance.MEDIUM,
        emergency_fund=10_000_000,
        expenses=[Expense("living", 8_000_000, ExpenseClass.FIXED)],
    )


async def test_forecast_uses_prophet_history_not_flat_base():
    pytest.importorskip("prophet")
    history = [
        MonthlyCashflowPoint(f"2025-{m:02d}", 5_000_000 + m * 200_000)
        for m in range(1, 9)
    ]
    service = ForecastService(
        FixedClock(date(2026, 6, 6)),
        InMemoryObligationRepository(),
        base_forecaster=ProphetCashflowForecaster(),
        history_provider=_FakeProvider(history),
    )

    result = await service.forecast(_profile(), months=3)
    nets = [month.net_cashflow for month in result.months]

    assert len(nets) == 3
    # Prophet projects from the ~5-6.4M history, so net cashflow is NOT the flat
    # current base of 12M.
    assert all(net != 12_000_000 for net in nets)
    assert result.summary.next_30_net == nets[0]
