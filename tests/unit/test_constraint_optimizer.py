from __future__ import annotations

from datetime import date

from app.core.clock import FixedClock
from app.modules.forecasting.application.services import ForecastService
from app.modules.obligations.infrastructure.memory_repository import InMemoryObligationRepository
from app.modules.planning.application.optimizer import ConstraintOptimizer
from app.modules.planning.application.simulator import ScenarioSimulator
from app.modules.profiles.domain.entities import Asset, Expense, FinancialProfile, Income
from app.modules.profiles.domain.value_objects import (
    AssetType,
    ExpenseClass,
    Liquidity,
    RiskTolerance,
)


def _optimizer() -> ConstraintOptimizer:
    clock = FixedClock(date(2026, 6, 6))
    repo = InMemoryObligationRepository()
    forecast = ForecastService(clock, repo)
    return ConstraintOptimizer(ScenarioSimulator(clock, forecast))


def _profile(
    salary: int = 20_000_000,
    cash: int = 40_000_000,
    expense: int = 10_000_000,
) -> FinancialProfile:
    return FinancialProfile(
        id="p1",
        income=Income(salary),
        risk=RiskTolerance.MEDIUM,
        emergency_fund=5_000_000,
        expenses=[Expense("living", expense, ExpenseClass.FIXED)],
        assets=[Asset(AssetType.CASH, cash, Liquidity.HIGH)],
    )


async def test_optimizer_recommends_best_non_blocked_scenario():
    result = await _optimizer().recommend(_profile(), "Phone", 15_000_000, horizon_months=6)

    # At 0% APR every tenor costs the same, so the safest-cashflow plan
    # (lowest monthly payment) wins.
    assert result.best_scenario_id == "bnpl_12m"
    by_id = {decision.scenario.scenario_id: decision for decision in result.scenarios}
    assert by_id["bnpl_12m"].recommended is True
    assert by_id["pay_full"].blocked is True
    assert "EFR_BELOW_LIMIT" in by_id["pay_full"].reason_codes


async def test_optimizer_blocks_dti_above_limit():
    result = await _optimizer().recommend(_profile(), "Laptop", 30_000_000, horizon_months=6)
    by_id = {decision.scenario.scenario_id: decision for decision in result.scenarios}

    assert by_id["bnpl_3m"].blocked is True
    assert "DTI_ABOVE_LIMIT" in by_id["bnpl_3m"].reason_codes


async def test_optimizer_uses_forecast_buffer_when_liquidity_is_missing():
    profile = FinancialProfile(
        id="p1",
        income=Income(100_000_000),
        risk=RiskTolerance.MEDIUM,
        expenses=[Expense("living", 10_000_000, ExpenseClass.FIXED)],
        assets=[],
        emergency_fund=0,
    )

    result = await _optimizer().recommend(profile, "Small purchase", 10_000_000, horizon_months=6)
    by_id = {decision.scenario.scenario_id: decision for decision in result.scenarios}

    assert result.best_scenario_id is not None
    assert by_id["bnpl_6m"].scenario.metrics.efr_after > 3
    assert "EFR_BELOW_LIMIT" not in by_id["bnpl_6m"].reason_codes


async def test_optimizer_returns_no_best_when_all_scenarios_blocked():
    result = await _optimizer().recommend(
        _profile(salary=5_000_000, cash=1_000_000, expense=4_000_000),
        "Phone",
        30_000_000,
        horizon_months=6,
    )

    assert result.best_scenario_id is None
    assert all(decision.blocked for decision in result.scenarios)
    assert "Không có phương án" in result.summary
