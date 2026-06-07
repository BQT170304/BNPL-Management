from __future__ import annotations

from datetime import date

import pytest

from app.core.clock import FixedClock
from app.modules.forecasting.application.services import ForecastService
from app.modules.obligations.domain.entities import (
    Obligation,
    ObligationStatus,
    ObligationType,
)
from app.modules.obligations.infrastructure.memory_repository import InMemoryObligationRepository
from app.modules.profiles.domain.entities import Asset, Debt, Expense, FinancialProfile, Income
from app.modules.profiles.domain.value_objects import (
    AssetType,
    DebtType,
    ExpenseClass,
    Liquidity,
    RiskTolerance,
)


def _profile(pid: str = "p1", salary: int = 20_000_000) -> FinancialProfile:
    return FinancialProfile(
        id=pid,
        income=Income(salary),
        risk=RiskTolerance.MEDIUM,
        emergency_fund=5_000_000,
        expenses=[
            Expense("rent", 6_000_000, ExpenseClass.FIXED),
            Expense("food", 4_000_000, ExpenseClass.SEMI_FIXED),
        ],
        debts=[
            Debt("loan", 2_000_000, 20_000_000, 12.0, 10, DebtType.INSTALLMENT),
        ],
        assets=[Asset(AssetType.CASH, 10_000_000, Liquidity.HIGH)],
    )


def _obligation(
    oid: str,
    start_date: date,
    remaining_terms: int | None = 6,
    status: ObligationStatus = ObligationStatus.ACTIVE,
    monthly_payment: int = 2_500_000,
) -> Obligation:
    return Obligation(
        id=oid,
        profile_id="p1",
        type=ObligationType.BNPL,
        merchant="Phone Store",
        category="electronics",
        principal_amount=15_000_000,
        monthly_payment=monthly_payment,
        due_day=25,
        start_date=start_date,
        remaining_terms=remaining_terms,
        status=status,
    )


@pytest.fixture
def service_and_repo() -> tuple[ForecastService, InMemoryObligationRepository]:
    repo = InMemoryObligationRepository()
    service = ForecastService(FixedClock(date(2026, 6, 6)), repo)
    return service, repo


async def test_forecast_starts_next_month_and_rolls_balance(
    service_and_repo: tuple[ForecastService, InMemoryObligationRepository],
):
    service, repo = service_and_repo
    await repo.add(_obligation("obl_1", date(2026, 7, 1)))

    forecast = await service.forecast(_profile(), months=2)

    assert [m.month for m in forecast.months] == ["2026-07", "2026-08"]
    assert forecast.months[0].starting_balance == 10_000_000
    assert forecast.months[0].obligation_payment == 2_500_000
    assert forecast.months[0].net_cashflow == 5_500_000
    assert forecast.months[0].ending_balance == 15_500_000
    assert forecast.months[1].starting_balance == 15_500_000


async def test_forecast_honors_remaining_terms(
    service_and_repo: tuple[ForecastService, InMemoryObligationRepository],
):
    service, repo = service_and_repo
    await repo.add(_obligation("obl_1", date(2026, 7, 1), remaining_terms=1))

    forecast = await service.forecast(_profile(), months=2)

    assert [m.obligation_payment for m in forecast.months] == [2_500_000, 0]


async def test_forecast_ignores_paused_obligations(
    service_and_repo: tuple[ForecastService, InMemoryObligationRepository],
):
    service, repo = service_and_repo
    await repo.add(_obligation("obl_1", date(2026, 7, 1), status=ObligationStatus.PAUSED))

    forecast = await service.forecast(_profile(), months=1)

    assert forecast.months[0].obligation_payment == 0


async def test_forecast_warns_for_negative_cashflow_and_balance(
    service_and_repo: tuple[ForecastService, InMemoryObligationRepository],
):
    service, repo = service_and_repo
    await repo.add(_obligation("obl_1", date(2026, 7, 1), monthly_payment=8_000_000))

    forecast = await service.forecast(_profile(salary=12_000_000), months=1)

    assert forecast.months[0].net_cashflow == -8_000_000
    assert forecast.months[0].ending_balance == 2_000_000
    assert forecast.months[0].warnings == ["NEGATIVE_NET_CASHFLOW"]


async def test_forecast_rejects_invalid_horizon(
    service_and_repo: tuple[ForecastService, InMemoryObligationRepository],
):
    service, _ = service_and_repo

    with pytest.raises(ValueError, match="months"):
        await service.forecast(_profile(), months=0)
