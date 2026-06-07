from __future__ import annotations

from datetime import date

import pytest

from app.core.clock import FixedClock
from app.core.errors import DecisionNotFound
from app.modules.decisions.application.services import DecisionService
from app.modules.decisions.infrastructure.memory_repository import InMemoryDecisionRepository
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


def _profile() -> FinancialProfile:
    return FinancialProfile(
        id="p1",
        income=Income(20_000_000),
        risk=RiskTolerance.MEDIUM,
        expenses=[Expense("living", 10_000_000, ExpenseClass.FIXED)],
        assets=[Asset(AssetType.CASH, 40_000_000, Liquidity.HIGH)],
    )


async def _recommendation():
    clock = FixedClock(date(2026, 6, 6))
    optimizer = ConstraintOptimizer(
        ScenarioSimulator(clock, ForecastService(clock, InMemoryObligationRepository()))
    )
    return await optimizer.recommend(_profile(), "Phone", 15_000_000)


async def test_record_and_get_decision_trace():
    service = DecisionService(InMemoryDecisionRepository())
    recommendation = await _recommendation()

    trace = await service.record(recommendation, {"profile_id": "p1"})
    fetched = await service.get(trace.id)

    assert fetched.id == trace.id
    assert fetched.recommendation.best_scenario_id == recommendation.best_scenario_id
    assert fetched.input_snapshot == {"profile_id": "p1"}


async def test_get_missing_decision_raises():
    service = DecisionService(InMemoryDecisionRepository())

    with pytest.raises(DecisionNotFound):
        await service.get("dec_missing")


async def test_explain_decision_uses_trace_numbers():
    service = DecisionService(InMemoryDecisionRepository())
    trace = await service.record(await _recommendation(), {"profile_id": "p1"})

    explanation = await service.explain(trace.id)

    assert explanation.decision_id == trace.id
    assert "Khuyến nghị" in explanation.summary
    assert any("DTI" in reason for reason in explanation.key_reasons)
    assert explanation.counterfactuals
