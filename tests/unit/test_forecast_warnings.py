from __future__ import annotations

from datetime import date

from app.core.clock import FixedClock
from app.modules.forecasting.application.services import ForecastService
from app.modules.forecasting.domain.projection import ForecastSummary, MonthlyProjection
from app.modules.forecasting.domain.warnings import ForecastAlertLevel, forecast_alerts
from app.modules.obligations.infrastructure.memory_repository import InMemoryObligationRepository
from app.modules.profiles.domain.entities import Asset, Debt, Expense, FinancialProfile, Income
from app.modules.profiles.domain.value_objects import (
    AssetType,
    DebtType,
    ExpenseClass,
    Liquidity,
    RiskTolerance,
)

CLOCK = FixedClock(date(2026, 1, 15))


def _profile(
    *,
    salary: int,
    expenses: list[Expense],
    debts: list[Debt] | None = None,
    cash: int = 0,
    emergency_fund: int = 0,
) -> FinancialProfile:
    return FinancialProfile(
        id="p1",
        income=Income(salary),
        risk=RiskTolerance.MEDIUM,
        emergency_fund=emergency_fund,
        expenses=expenses,
        debts=debts or [],
        assets=[Asset(AssetType.CASH, cash, Liquidity.HIGH)] if cash else [],
    )


async def _forecast(profile: FinancialProfile, months: int = 6):
    service = ForecastService(clock=CLOCK, obligations=InMemoryObligationRepository())
    return await service.forecast(profile, months=months)


def test_summary_from_projections():
    months = [
        MonthlyProjection("2026-02", 10, 0, 0, 0, 5, 100, 105),
        MonthlyProjection("2026-03", 10, 0, 0, 0, -3, 105, 102),
        MonthlyProjection("2026-04", 10, 0, 0, 0, 8, 102, 110),
        MonthlyProjection("2026-05", 10, 0, 0, 0, -20, 110, 90),
    ]
    summary = ForecastSummary.from_projections(months)
    assert summary.next_30_net == 5
    assert summary.next_90_net == 5 - 3 + 8
    assert summary.min_projected_balance == 90


def test_summary_empty():
    summary = ForecastSummary.from_projections([])
    assert summary == ForecastSummary(0, 0, 0)


async def test_projected_negative_balance_alert():
    profile = _profile(
        salary=10_000_000,
        expenses=[Expense("rent", 13_000_000, ExpenseClass.FIXED)],
        emergency_fund=2_000_000,
    )
    forecast = await _forecast(profile)
    alerts = forecast_alerts(forecast, profile)
    codes = {a.code for a in alerts}
    assert "PROJECTED_NEGATIVE_BALANCE" in codes
    negative = next(a for a in alerts if a.code == "PROJECTED_NEGATIVE_BALANCE")
    assert negative.level == ForecastAlertLevel.CRITICAL
    assert negative.month is not None


async def test_projected_low_buffer_alert():
    profile = _profile(
        salary=10_000_000,
        expenses=[Expense("rent", 9_500_000, ExpenseClass.FIXED)],
        cash=1_000_000,
    )
    forecast = await _forecast(profile)
    alerts = forecast_alerts(forecast, profile, safe_months=3)
    codes = {a.code for a in alerts}
    assert "PROJECTED_LOW_BUFFER" in codes
    assert "PROJECTED_NEGATIVE_BALANCE" not in codes


async def test_projected_dti_pressure_alert():
    profile = _profile(
        salary=10_000_000,
        expenses=[Expense("rent", 1_000_000, ExpenseClass.FIXED)],
        debts=[Debt("loan", 4_500_000, 50_000_000, 18.0, 24, DebtType.INSTALLMENT)],
        cash=100_000_000,
    )
    forecast = await _forecast(profile)
    alerts = forecast_alerts(forecast, profile, dti_limit=40.0)
    codes = {a.code for a in alerts}
    assert "PROJECTED_DTI_PRESSURE" in codes
    assert "PROJECTED_NEGATIVE_BALANCE" not in codes
    assert "PROJECTED_LOW_BUFFER" not in codes


async def test_healthy_profile_has_no_forecast_alerts():
    profile = _profile(
        salary=30_000_000,
        expenses=[Expense("rent", 5_000_000, ExpenseClass.FIXED)],
        cash=200_000_000,
    )
    forecast = await _forecast(profile)
    assert forecast_alerts(forecast, profile) == []
