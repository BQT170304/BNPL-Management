# app/modules/analysis/application/services.py
from __future__ import annotations

from app.core.clock import Clock
from app.modules.analysis.domain import formulas as f
from app.modules.analysis.domain.allocation import AllocationStrategy
from app.modules.analysis.domain.results import GoalMetric, ProfileMetrics
from app.modules.analysis.domain.thresholds import classify_dti
from app.modules.profiles.domain.entities import FinancialProfile


class AnalysisService:
    """Assembles deterministic ProfileMetrics from a profile at a point in time."""

    def __init__(self, clock: Clock, allocation: AllocationStrategy) -> None:
        self._clock = clock
        self._allocation = allocation

    def analyze(self, profile: FinancialProfile, new_payment: int = 0) -> ProfileMetrics:
        today = self._clock.today()
        income = profile.total_income
        base_ncf = f.net_cash_flow(income, profile.total_expense, profile.total_debt_payment)
        ncf = base_ncf - new_payment

        dti_value = f.dti(profile.total_debt_payment + new_payment, income)
        saving = f.saving_rate(base_ncf, new_payment, income)
        efr_value = f.efr(profile.emergency_fund, profile.essential_expense)

        allocation = self._allocation.allocate(ncf, profile.goals)
        goal_metrics: list[GoalMetric] = []
        weighted: list[tuple[float, int]] = []
        flags: list[str] = []
        if ncf < 0:
            flags.append("NEGATIVE_CASHFLOW")

        for goal in profile.goals:
            months = goal.months_remaining(today)
            monthly = allocation.get(goal.id, 0)
            gap = f.goal_gap(goal.target_amount, goal.savings_allocated)
            if ncf < 0:
                grs_value, gat_value, delay = 100.0, float("inf"), float("inf")
            else:
                gat_value = f.gat(gap, monthly)
                delay = f.goal_delay(gat_value, months)
                grs_value = f.grs(delay, months)
            goal_metrics.append(GoalMetric(
                goal_id=goal.id, name=goal.name, gap=gap, monthly_allocated=monthly,
                gat=gat_value, delay=delay, grs=grs_value, months_remaining=months,
            ))
            weighted.append((grs_value, goal.priority.weight))

        return ProfileMetrics(
            ncf=ncf,
            dti=dti_value,
            dti_band=classify_dti(dti_value),
            saving_rate=saving,
            efr=efr_value,
            pgrs=f.pgrs(weighted),
            goals=goal_metrics,
            flags=flags,
        )
