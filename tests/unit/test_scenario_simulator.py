from __future__ import annotations

from datetime import date

import pytest

from app.core.clock import FixedClock
from app.modules.analysis.application.services import AnalysisService
from app.modules.analysis.domain.allocation import EvenAllocation
from app.modules.forecasting.application.services import ForecastService
from app.modules.goals.domain.entities import Goal, Priority
from app.modules.obligations.infrastructure.memory_repository import InMemoryObligationRepository
from app.modules.planning.application.simulator import ScenarioSimulator
from app.modules.profiles.domain.entities import Asset, Expense, FinancialProfile, Income
from app.modules.profiles.domain.value_objects import (
    AssetType,
    ExpenseClass,
    Liquidity,
    RiskTolerance,
)


def _profile(cash: int = 20_000_000) -> FinancialProfile:
    return FinancialProfile(
        id="p1",
        income=Income(20_000_000),
        risk=RiskTolerance.MEDIUM,
        emergency_fund=5_000_000,
        expenses=[
            Expense("rent", 6_000_000, ExpenseClass.FIXED),
            Expense("food", 4_000_000, ExpenseClass.SEMI_FIXED),
        ],
        assets=[Asset(AssetType.CASH, cash, Liquidity.HIGH)],
    )


@pytest.fixture
def simulator() -> ScenarioSimulator:
    clock = FixedClock(date(2026, 6, 6))
    repo = InMemoryObligationRepository()
    forecast = ForecastService(clock, repo)
    return ScenarioSimulator(clock, forecast)


async def test_simulator_generates_default_scenarios(simulator: ScenarioSimulator):
    result = await simulator.simulate(_profile(), "Phone", 15_000_000, horizon_months=6)

    assert [scenario.scenario_id for scenario in result.scenarios] == [
        "pay_full",
        "bnpl_3m",
        "bnpl_6m",
        "bnpl_12m",
        "down_30_bnpl_6m",
        "delay_1m_bnpl_6m",
    ]


async def test_simulator_calculates_monthly_payments(simulator: ScenarioSimulator):
    result = await simulator.simulate(_profile(), "Phone", 15_000_000, horizon_months=6)
    by_id = {scenario.scenario_id: scenario for scenario in result.scenarios}

    assert by_id["pay_full"].upfront_payment == 15_000_000
    assert by_id["pay_full"].monthly_payment == 0
    assert by_id["bnpl_3m"].monthly_payment == 5_000_000
    assert by_id["bnpl_6m"].monthly_payment == 2_500_000
    assert by_id["bnpl_12m"].monthly_payment == 1_250_000
    assert by_id["down_30_bnpl_6m"].upfront_payment == 4_500_000
    assert by_id["down_30_bnpl_6m"].monthly_payment == 1_750_000


async def test_delay_scenario_starts_one_month_later(simulator: ScenarioSimulator):
    result = await simulator.simulate(_profile(), "Phone", 15_000_000, horizon_months=2)
    by_id = {scenario.scenario_id: scenario for scenario in result.scenarios}

    delay = by_id["delay_1m_bnpl_6m"]

    assert delay.start_month == "2026-08"
    assert [month.obligation_payment for month in delay.forecast] == [0, 2_500_000]


async def test_pay_full_warns_when_upfront_exceeds_liquid_balance(
    simulator: ScenarioSimulator,
):
    result = await simulator.simulate(_profile(cash=5_000_000), "Phone", 15_000_000)
    by_id = {scenario.scenario_id: scenario for scenario in result.scenarios}

    assert "UPFRONT_EXCEEDS_LIQUID_BALANCE" in by_id["pay_full"].warnings


async def test_simulator_calculates_goal_delay_impact():
    clock = FixedClock(date(2026, 6, 6))
    repo = InMemoryObligationRepository()
    simulator = ScenarioSimulator(
        clock,
        ForecastService(clock, repo),
        AnalysisService(clock, EvenAllocation()),
    )
    profile = _profile()
    profile.goals = [
        Goal(
            id="g1",
            name="Emergency",
            target_amount=200_000_000,
            deadline=date(2027, 6, 1),
            priority=Priority.HIGH,
            savings_allocated=0,
        )
    ]

    result = await simulator.simulate(profile, "Phone", 15_000_000, horizon_months=6)
    by_id = {scenario.scenario_id: scenario for scenario in result.scenarios}

    assert by_id["bnpl_6m"].metrics.goal_delay_months > 0


async def test_simulator_rejects_invalid_amount(simulator: ScenarioSimulator):
    with pytest.raises(ValueError, match="amount"):
        await simulator.simulate(_profile(), "Phone", 0)
