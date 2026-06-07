from __future__ import annotations

import calendar
import math
from dataclasses import dataclass
from datetime import date

from app.core.clock import Clock
from app.core.money import ratio
from app.modules.analysis.application.services import AnalysisService
from app.modules.forecasting.application.services import ForecastService
from app.modules.forecasting.domain.projection import MonthlyProjection
from app.modules.obligations.domain.entities import Obligation, ObligationType
from app.modules.planning.domain.cost import FinancingTerms, compute_cost
from app.modules.planning.domain.scenarios import (
    ScenarioMetrics,
    ScenarioResult,
    SimulationResult,
)
from app.modules.profiles.domain.entities import FinancialProfile
from app.modules.profiles.domain.value_objects import AssetType


def _add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _month_start(value: date) -> date:
    return date(value.year, value.month, 1)


def _month_key(value: date) -> str:
    return f"{value.year:04d}-{value.month:02d}"


def _liquid_balance(profile: FinancialProfile) -> int:
    liquid_assets = sum(
        asset.value
        for asset in profile.assets
        if asset.type in (AssetType.CASH, AssetType.SAVINGS)
    )
    return liquid_assets if liquid_assets > 0 else profile.emergency_fund


@dataclass(frozen=True)
class _Candidate:
    scenario_id: str
    label: str
    upfront: int
    principal: int
    months: int | None
    start_offset_months: int


class ScenarioSimulator:
    def __init__(
        self,
        clock: Clock,
        forecast: ForecastService,
        analysis: AnalysisService | None = None,
    ) -> None:
        self._clock = clock
        self._forecast = forecast
        self._analysis = analysis

    async def simulate(
        self,
        profile: FinancialProfile,
        item_name: str,
        amount: int,
        horizon_months: int = 6,
        terms: FinancingTerms | None = None,
        tenor: int | None = None,
    ) -> SimulationResult:
        if amount <= 0:
            raise ValueError("amount must be > 0")
        if horizon_months <= 0:
            raise ValueError("horizon_months must be > 0")
        terms = terms or FinancingTerms()

        scenarios: list[ScenarioResult] = []
        for candidate in self._candidates(amount, tenor):
            scenarios.append(
                await self._simulate_candidate(
                    profile, item_name, amount, candidate, horizon_months, terms
                )
            )

        return SimulationResult(
            profile_id=profile.id,
            item_name=item_name,
            amount=amount,
            scenarios=scenarios,
        )

    def _candidates(self, amount: int, tenor: int | None) -> list[_Candidate]:
        down_payment = math.ceil(amount * 0.30)
        candidates = [
            _Candidate("pay_full", "Trả thẳng", amount, 0, None, 1),
            _Candidate("bnpl_3m", "BNPL 3 tháng", 0, amount, 3, 1),
            _Candidate("bnpl_6m", "BNPL 6 tháng", 0, amount, 6, 1),
            _Candidate("bnpl_12m", "BNPL 12 tháng", 0, amount, 12, 1),
            _Candidate(
                "down_30_bnpl_6m",
                "Trả trước 30% + BNPL 6 tháng",
                down_payment,
                amount - down_payment,
                6,
                1,
            ),
            _Candidate("delay_1m_bnpl_6m", "Hoãn 1 tháng + BNPL 6 tháng", 0, amount, 6, 2),
        ]
        if tenor is not None and tenor > 0 and tenor not in {3, 6, 12}:
            candidates.append(
                _Candidate(f"bnpl_{tenor}m", f"BNPL {tenor} tháng", 0, amount, tenor, 1)
            )
        return candidates

    async def _simulate_candidate(
        self,
        profile: FinancialProfile,
        item_name: str,
        amount: int,
        candidate: _Candidate,
        horizon_months: int,
        terms: FinancingTerms,
    ) -> ScenarioResult:
        start_date = _month_start(_add_months(self._clock.today(), candidate.start_offset_months))
        cost = compute_cost(
            amount=amount,
            upfront=candidate.upfront,
            principal=candidate.principal,
            months=candidate.months,
            terms=terms,
        )
        monthly_payment = cost.monthly_payment
        extra_obligations = []
        if candidate.months and monthly_payment > 0:
            extra_obligations.append(Obligation(
                id=f"scenario_{candidate.scenario_id}",
                profile_id=profile.id,
                type=ObligationType.BNPL,
                merchant=item_name,
                category="purchase",
                principal_amount=candidate.principal,
                monthly_payment=monthly_payment,
                due_day=25,
                start_date=start_date,
                remaining_terms=candidate.months,
                apr=terms.apr,
            ))

        forecast = await self._forecast.forecast(
            profile,
            months=horizon_months,
            extra_obligations=extra_obligations,
            starting_balance_adjustment=-candidate.upfront,
        )
        warnings = self._scenario_warnings(profile, candidate, forecast.months)
        return ScenarioResult(
            scenario_id=candidate.scenario_id,
            label=candidate.label,
            upfront_payment=candidate.upfront,
            monthly_payment=monthly_payment,
            duration_months=candidate.months,
            start_month=_month_key(start_date) if candidate.months else None,
            forecast=forecast.months,
            metrics=self._metrics(
                profile,
                candidate.upfront,
                monthly_payment,
                forecast.months,
            ),
            cost=cost,
            warnings=warnings,
        )

    def _scenario_warnings(
        self,
        profile: FinancialProfile,
        candidate: _Candidate,
        forecast: list[MonthlyProjection],
    ) -> list[str]:
        warnings = sorted({warning for month in forecast for warning in month.warnings})
        if candidate.upfront > _liquid_balance(profile):
            warnings.append("UPFRONT_EXCEEDS_LIQUID_BALANCE")
        return warnings

    def _metrics(
        self,
        profile: FinancialProfile,
        upfront: int,
        monthly_payment: int,
        forecast: list[MonthlyProjection],
    ) -> ScenarioMetrics:
        min_balance = min(month.ending_balance for month in forecast)
        max_dti = ratio(profile.total_debt_payment + monthly_payment, profile.total_income) * 100.0
        essential = profile.essential_expense
        current_liquid = _liquid_balance(profile)
        efr_buffer = (
            max(0, current_liquid - upfront)
            if current_liquid > 0
            else max(0, min_balance)
        )
        efr_after = ratio(efr_buffer, essential)
        return ScenarioMetrics(
            min_balance=min_balance,
            max_dti=max_dti,
            efr_after=efr_after,
            goal_delay_months=self._goal_delay_months(profile, monthly_payment),
        )

    def _goal_delay_months(self, profile: FinancialProfile, monthly_payment: int) -> float:
        if self._analysis is None or not profile.goals:
            return 0.0
        current = self._analysis.analyze(profile)
        impacted = self._analysis.analyze(profile, new_payment=monthly_payment)
        current_by_id = {goal.goal_id: goal for goal in current.goals}
        deltas: list[float] = []
        for goal in impacted.goals:
            previous = current_by_id.get(goal.goal_id)
            if previous is None:
                continue
            if goal.delay == float("inf"):
                deltas.append(float(goal.months_remaining))
            else:
                deltas.append(max(0.0, goal.delay - previous.delay))
        return round(max(deltas, default=0.0), 2)
