from __future__ import annotations

from datetime import date

from app.core.clock import FixedClock
from app.modules.analysis.application.services import AnalysisService
from app.modules.analysis.domain.allocation import get_strategy
from app.modules.copilot.application.services import CopilotService
from app.modules.copilot.domain.intents import CopilotTool
from app.modules.decisions.application.services import DecisionService
from app.modules.decisions.infrastructure.memory_repository import InMemoryDecisionRepository
from app.modules.forecasting.application.services import ForecastService
from app.modules.obligations.application.services import ObligationService
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
from app.modules.profiles.infrastructure.memory_repository import InMemoryProfileRepository

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


async def _service(with_profile: bool = True) -> CopilotService:
    profiles = InMemoryProfileRepository()
    if with_profile:
        await profiles.add(_profile())
    ob_repo = InMemoryObligationRepository()
    forecast = ForecastService(CLOCK, ob_repo)
    optimizer = ConstraintOptimizer(ScenarioSimulator(CLOCK, forecast), obligations=ob_repo)
    analysis = AnalysisService(CLOCK, get_strategy("weighted"))
    return CopilotService(
        profiles=profiles,
        optimizer=optimizer,
        decisions=DecisionService(InMemoryDecisionRepository()),
        forecast=forecast,
        analysis=analysis,
        obligations=ObligationService(ob_repo, profiles),
    )


async def test_purchase_question_runs_optimizer():
    service = await _service()
    reply = await service.chat(
        "Tôi có nên mua điện thoại 15 triệu trả góp 6 tháng không?",
        profile_id="p1",
    )
    assert reply.tool == CopilotTool.RECOMMEND
    assert reply.used_optimizer is True
    assert reply.decision_id is not None


async def test_no_self_approval_without_profile():
    service = await _service()
    reply = await service.chat("Tôi có nên mua điện thoại 15 triệu không?")
    # Guardrail: cannot approve without running the optimizer.
    assert reply.tool == CopilotTool.CLARIFY
    assert reply.used_optimizer is False
    assert reply.decision_id is None
    assert "approve" not in reply.reply.lower()


async def test_no_self_approval_without_amount():
    service = await _service()
    reply = await service.chat("Tôi có nên mua điện thoại không?", profile_id="p1")
    assert reply.tool == CopilotTool.CLARIFY
    assert reply.used_optimizer is False
    assert reply.decision_id is None
