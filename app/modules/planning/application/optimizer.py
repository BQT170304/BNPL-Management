from __future__ import annotations

from app.core.money import percent
from app.modules.obligations.application.ports import ObligationRepository
from app.modules.planning.application.simulator import ScenarioSimulator
from app.modules.planning.domain.constraints import (
    RecommendationResult,
    ScenarioDecision,
    ScoreBreakdown,
)
from app.modules.planning.domain.cost import FinancingTerms
from app.modules.planning.domain.scenarios import ScenarioResult
from app.modules.profiles.domain.entities import FinancialProfile


def _clamp_score(value: float) -> float:
    return max(0.0, min(100.0, value))


class ConstraintOptimizer:
    def __init__(
        self,
        simulator: ScenarioSimulator,
        obligations: ObligationRepository | None = None,
        low_confidence_threshold: float = 0.7,
    ) -> None:
        self._simulator = simulator
        self._obligations = obligations
        self._low_confidence_threshold = low_confidence_threshold

    async def recommend(
        self,
        profile: FinancialProfile,
        item_name: str,
        amount: int,
        horizon_months: int = 6,
        terms: FinancingTerms | None = None,
        tenor: int | None = None,
    ) -> RecommendationResult:
        simulation = await self._simulator.simulate(
            profile,
            item_name=item_name,
            amount=amount,
            horizon_months=horizon_months,
            terms=terms,
            tenor=tenor,
        )
        decisions = [
            self._decide(profile, scenario, simulation.amount)
            for scenario in simulation.scenarios
        ]
        eligible = [decision for decision in decisions if not decision.blocked]
        ranked = sorted(eligible, key=lambda decision: decision.score, reverse=True)
        best = ranked[0] if ranked else None
        scenarios = [
            ScenarioDecision(
                scenario=decision.scenario,
                score=decision.score,
                recommended=best is not None
                and decision.scenario.scenario_id == best.scenario.scenario_id,
                blocked=decision.blocked,
                reason_codes=decision.reason_codes,
                score_breakdown=decision.score_breakdown,
            )
            for decision in decisions
        ]
        min_confidence, low_names = await self._confidence(profile, scenarios)
        advisories = self._advisories(min_confidence, low_names)
        return RecommendationResult(
            profile_id=simulation.profile_id,
            item_name=simulation.item_name,
            amount=simulation.amount,
            best_scenario_id=best.scenario.scenario_id if best else None,
            summary=self._summary(best),
            scenarios=scenarios,
            simulation=simulation,
            advisories=advisories,
            min_confidence=min_confidence,
            low_confidence_obligations=low_names,
        )

    async def _confidence(
        self,
        profile: FinancialProfile,
        scenarios: list[ScenarioDecision],
    ) -> tuple[float, list[str]]:
        """Propagate obligation confidence into the decision.

        Prefer naming the uncertain obligations (when an obligation repository
        is wired); otherwise fall back to the forecast's per-month
        LOW_CONFIDENCE_OBLIGATION marker so the advisory is never silently lost.
        """

        if self._obligations is not None:
            obligations = await self._obligations.list_by_profile(profile.id)
            if obligations:
                min_confidence = min(o.confidence for o in obligations)
                low_names = sorted({
                    o.merchant
                    for o in obligations
                    if o.confidence < self._low_confidence_threshold
                })
                return min_confidence, low_names

        flagged = any(
            "LOW_CONFIDENCE_OBLIGATION" in decision.scenario.warnings
            for decision in scenarios
        )
        return (0.0 if flagged else 1.0), []

    def _advisories(self, min_confidence: float, low_names: list[str]) -> list[str]:
        has_low = bool(low_names) or min_confidence < self._low_confidence_threshold
        if not has_low:
            return []
        return ["LOW_CONFIDENCE_OBLIGATION", "VERIFY_OBLIGATION_BEFORE_DECISION"]

    def _decide(
        self,
        profile: FinancialProfile,
        scenario: ScenarioResult,
        amount: int,
    ) -> ScenarioDecision:
        reason_codes = self._hard_reason_codes(scenario)
        breakdown = self._score_breakdown(profile, scenario, amount)
        return ScenarioDecision(
            scenario=scenario,
            score=breakdown.weighted_total,
            recommended=False,
            blocked=bool(reason_codes),
            reason_codes=reason_codes,
            score_breakdown=breakdown,
        )

    def _hard_reason_codes(self, scenario: ScenarioResult) -> list[str]:
        reasons: list[str] = []
        if scenario.metrics.min_balance < 0:
            reasons.append("NEGATIVE_BALANCE")
        if "NEGATIVE_NET_CASHFLOW" in scenario.warnings:
            reasons.append("NEGATIVE_NET_CASHFLOW")
        if scenario.metrics.max_dti > 40:
            reasons.append("DTI_ABOVE_LIMIT")
        if scenario.metrics.efr_after < 3:
            reasons.append("EFR_BELOW_LIMIT")
        if "UPFRONT_EXCEEDS_LIQUID_BALANCE" in scenario.warnings:
            reasons.append("UPFRONT_EXCEEDS_LIQUID_BALANCE")
        return reasons

    def _score_breakdown(
        self,
        profile: FinancialProfile,
        scenario: ScenarioResult,
        amount: int,
    ) -> ScoreBreakdown:
        income = profile.total_income
        monthly_pressure = percent(scenario.monthly_payment, income)
        return ScoreBreakdown(
            cashflow_safety=_clamp_score(percent(max(0, scenario.metrics.min_balance), income)),
            obligation_pressure=_clamp_score(100.0 - monthly_pressure * 2.0),
            goal_impact=_clamp_score(100.0 - scenario.metrics.goal_delay_months * 10.0),
            emergency_fund=self._efr_score(scenario.metrics.efr_after),
            total_cost=self._cost_score(scenario, amount),
        )

    def _cost_score(self, scenario: ScenarioResult, amount: int) -> float:
        """Reward scenarios whose true cost is close to the cash price."""

        if amount <= 0:
            return 100.0
        premium_pct = (scenario.cost.total_cost - amount) / amount * 100.0
        return _clamp_score(100.0 - premium_pct * 2.0)

    def _efr_score(self, efr: float) -> float:
        if efr >= 6:
            return 100.0
        if efr >= 3:
            return 70.0
        if efr >= 1:
            return 30.0
        return 0.0

    def _summary(self, best: ScenarioDecision | None) -> str:
        if best is None:
            return "Không có phương án nào thỏa toàn bộ ràng buộc cứng."
        return (
            f"Khuyến nghị {best.scenario.label} "
            f"với điểm phù hợp {best.score:.1f}/100."
        )
