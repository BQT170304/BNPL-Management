from __future__ import annotations

from datetime import date

from app.core.clock import FixedClock
from app.modules.forecasting.application.services import ForecastService
from app.modules.obligations.infrastructure.memory_repository import InMemoryObligationRepository
from app.modules.planning.application.optimizer import ConstraintOptimizer
from app.modules.planning.application.simulator import ScenarioSimulator
from app.modules.planning.domain.cost import FinancingTerms
from app.modules.profiles.domain.entities import Asset, Expense, FinancialProfile, Income
from app.modules.profiles.domain.value_objects import (
    AssetType,
    ExpenseClass,
    Liquidity,
    RiskTolerance,
)


def _optimizer() -> ConstraintOptimizer:
    clock = FixedClock(date(2026, 6, 6))
    return ConstraintOptimizer(
        ScenarioSimulator(clock, ForecastService(clock, InMemoryObligationRepository()))
    )


def _profile() -> FinancialProfile:
    return FinancialProfile(
        id="p1",
        income=Income(20_000_000),
        risk=RiskTolerance.MEDIUM,
        emergency_fund=5_000_000,
        expenses=[Expense("living", 10_000_000, ExpenseClass.FIXED)],
        assets=[Asset(AssetType.CASH, 40_000_000, Liquidity.HIGH)],
    )


async def test_high_apr_makes_long_tenor_more_expensive():
    result = await _optimizer().recommend(
        _profile(), "Phone", 15_000_000, horizon_months=6,
        terms=FinancingTerms(apr=60.0, fee=500_000),
    )
    cost = {d.scenario.scenario_id: d.scenario.cost for d in result.scenarios}
    assert cost["bnpl_12m"].total_interest > cost["bnpl_6m"].total_interest
    assert cost["bnpl_12m"].total_cost > cost["bnpl_6m"].total_cost


async def test_high_apr_stops_long_bnpl_from_auto_winning():
    zero = await _optimizer().recommend(_profile(), "Phone", 15_000_000, horizon_months=6)
    assert zero.best_scenario_id == "bnpl_12m"

    expensive = await _optimizer().recommend(
        _profile(), "Phone", 15_000_000, horizon_months=6,
        terms=FinancingTerms(apr=60.0, fee=500_000),
    )
    # With a punitive APR the 12-month plan no longer wins on cost.
    assert expensive.best_scenario_id != "bnpl_12m"


async def test_custom_tenor_is_simulated():
    result = await _optimizer().recommend(
        _profile(), "Phone", 9_000_000, horizon_months=6, tenor=9,
    )
    ids = {d.scenario.scenario_id for d in result.scenarios}
    assert "bnpl_9m" in ids
