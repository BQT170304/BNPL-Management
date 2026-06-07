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

        # Compute per-metric status and overall health score
        def _ncf_score(ncf_val: int, inc: int) -> tuple[int, str]:
            if inc <= 0:
                return 0, "critical"
            rate = ncf_val / inc * 100
            if rate >= 20:
                return 100, "healthy"
            if rate >= 10:
                return 70, "warning"
            if rate >= 0:
                return 40, "warning"
            return 0, "critical"

        def _dti_score(d: float) -> tuple[int, str]:
            if d < 20:
                return 100, "healthy"
            if d < 35:
                return 70, "healthy"
            if d < 40:
                return 40, "warning"
            return 0, "critical"

        def _saving_score(rate: float) -> tuple[int, str]:
            if rate >= 20:
                return 100, "healthy"
            if rate >= 10:
                return 70, "warning"
            if rate >= 0:
                return 40, "warning"
            return 0, "critical"

        def _efr_score(e: float) -> tuple[int, str]:
            if e >= 6:
                return 100, "healthy"
            if e >= 3:
                return 70, "warning"
            if e >= 1:
                return 40, "warning"
            return 0, "critical"

        def _pgrs_score(p: float) -> tuple[int, str]:
            v = max(0, min(100, 100 - p))
            if v >= 70:
                return int(v), "healthy"
            if v >= 40:
                return int(v), "warning"
            return int(v), "critical"

        ncf_s, ncf_st = _ncf_score(ncf, income)
        dti_s, dti_st = _dti_score(dti_value)
        sav_s, sav_st = _saving_score(saving)
        efr_s, efr_st = _efr_score(efr_value)
        pgrs_val = f.pgrs(weighted)
        pgrs_s, pgrs_st = _pgrs_score(pgrs_val)

        overall = int(0.30 * ncf_s + 0.25 * dti_s + 0.20 * sav_s + 0.15 * efr_s + 0.10 * pgrs_s)
        statuses = {
            "ncf": ncf_st,
            "dti": dti_st,
            "saving_rate": sav_st,
            "efr": efr_st,
            "pgrs": pgrs_st,
        }

        return ProfileMetrics(
            ncf=ncf,
            dti=dti_value,
            dti_band=classify_dti(dti_value),
            saving_rate=saving,
            efr=efr_value,
            pgrs=pgrs_val,
            goals=goal_metrics,
            flags=flags,
            overall_health_score=overall,
            metric_statuses=statuses,
        )
