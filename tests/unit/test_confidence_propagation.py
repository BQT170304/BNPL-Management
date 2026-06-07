from __future__ import annotations

from datetime import date

from app.core.clock import FixedClock
from app.modules.forecasting.application.services import ForecastService
from app.modules.obligations.domain.entities import Obligation, ObligationType
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

CLOCK = FixedClock(date(2026, 6, 6))


def _profile() -> FinancialProfile:
    return FinancialProfile(
        id="p1",
        income=Income(20_000_000),
        risk=RiskTolerance.MEDIUM,
        emergency_fund=5_000_000,
        expenses=[Expense("living", 8_000_000, ExpenseClass.FIXED)],
        assets=[Asset(AssetType.CASH, 40_000_000, Liquidity.HIGH)],
    )


def _low_conf_obligation(confidence: float = 0.4) -> Obligation:
    return Obligation(
        id="auto_1",
        profile_id="p1",
        type=ObligationType.LOAN,
        merchant="tra gop dien may",
        category="debt",
        principal_amount=6_000_000,
        monthly_payment=500_000,
        due_day=10,
        start_date=date(2026, 1, 1),
        remaining_terms=24,
        confidence=confidence,
    )


async def test_forecast_marks_low_confidence_obligation():
    repo = InMemoryObligationRepository()
    await repo.add(_low_conf_obligation(0.4))
    service = ForecastService(CLOCK, repo, low_confidence_threshold=0.7)
    forecast = await service.forecast(_profile(), months=6)
    assert any("LOW_CONFIDENCE_OBLIGATION" in m.warnings for m in forecast.months)


async def test_forecast_does_not_mark_high_confidence():
    repo = InMemoryObligationRepository()
    await repo.add(_low_conf_obligation(0.95))
    service = ForecastService(CLOCK, repo, low_confidence_threshold=0.7)
    forecast = await service.forecast(_profile(), months=6)
    assert all("LOW_CONFIDENCE_OBLIGATION" not in m.warnings for m in forecast.months)


async def test_optimizer_propagates_confidence_and_advisories():
    repo = InMemoryObligationRepository()
    await repo.add(_low_conf_obligation(0.4))
    optimizer = ConstraintOptimizer(
        ScenarioSimulator(CLOCK, ForecastService(CLOCK, repo, low_confidence_threshold=0.7)),
        obligations=repo,
        low_confidence_threshold=0.7,
    )
    result = await optimizer.recommend(_profile(), "Phone", 9_000_000, horizon_months=6)
    assert result.min_confidence == 0.4
    assert "LOW_CONFIDENCE_OBLIGATION" in result.advisories
    assert "VERIFY_OBLIGATION_BEFORE_DECISION" in result.advisories
    assert "tra gop dien may" in result.low_confidence_obligations


async def test_optimizer_no_advisory_when_all_confident():
    repo = InMemoryObligationRepository()
    await repo.add(_low_conf_obligation(1.0))
    optimizer = ConstraintOptimizer(
        ScenarioSimulator(CLOCK, ForecastService(CLOCK, repo, low_confidence_threshold=0.7)),
        obligations=repo,
        low_confidence_threshold=0.7,
    )
    result = await optimizer.recommend(_profile(), "Phone", 9_000_000, horizon_months=6)
    assert result.min_confidence == 1.0
    assert result.advisories == []
    assert result.low_confidence_obligations == []
