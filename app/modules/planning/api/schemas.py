from __future__ import annotations

from pydantic import BaseModel, Field

from app.modules.forecasting.api.schemas import MonthlyProjectionOut
from app.modules.planning.domain.constraints import (
    RecommendationResult,
    ScenarioDecision,
    ScoreBreakdown,
)
from app.modules.planning.domain.cost import CostBreakdown, FinancingTerms
from app.modules.planning.domain.scenarios import (
    ScenarioMetrics,
    ScenarioResult,
    SimulationResult,
)


class SimulateIn(BaseModel):
    profile_id: str
    item_name: str = Field(min_length=1)
    amount: int = Field(gt=0)
    horizon_months: int = Field(default=6, ge=1, le=24)
    apr: float = Field(default=0.0, ge=0)
    fee: int = Field(default=0, ge=0)
    late_fee: int = Field(default=0, ge=0)
    merchant_subsidy: int = Field(default=0, ge=0)
    tenor: int | None = Field(default=None, ge=1, le=24)
    record: bool = True

    def to_terms(self) -> FinancingTerms:
        return FinancingTerms(
            apr=self.apr,
            fee=self.fee,
            late_fee=self.late_fee,
            merchant_subsidy=self.merchant_subsidy,
        )


class ScenarioMetricsOut(BaseModel):
    min_balance: int
    max_dti: float
    efr_after: float
    goal_delay_months: float

    @classmethod
    def from_domain(cls, metrics: ScenarioMetrics) -> ScenarioMetricsOut:
        return cls(
            min_balance=metrics.min_balance,
            max_dti=metrics.max_dti,
            efr_after=metrics.efr_after,
            goal_delay_months=metrics.goal_delay_months,
        )


class CostBreakdownOut(BaseModel):
    monthly_payment: int
    total_interest: int
    total_fee: int
    late_fee: int
    merchant_subsidy: int
    total_cost: int
    break_even_month: int | None

    @classmethod
    def from_domain(cls, cost: CostBreakdown) -> CostBreakdownOut:
        return cls(
            monthly_payment=cost.monthly_payment,
            total_interest=cost.total_interest,
            total_fee=cost.total_fee,
            late_fee=cost.late_fee,
            merchant_subsidy=cost.merchant_subsidy,
            total_cost=cost.total_cost,
            break_even_month=cost.break_even_month,
        )


class ScenarioOut(BaseModel):
    scenario_id: str
    label: str
    upfront_payment: int
    monthly_payment: int
    duration_months: int | None
    start_month: str | None
    forecast: list[MonthlyProjectionOut]
    metrics: ScenarioMetricsOut
    cost: CostBreakdownOut
    warnings: list[str]

    @classmethod
    def from_domain(cls, scenario: ScenarioResult) -> ScenarioOut:
        return cls(
            scenario_id=scenario.scenario_id,
            label=scenario.label,
            upfront_payment=scenario.upfront_payment,
            monthly_payment=scenario.monthly_payment,
            duration_months=scenario.duration_months,
            start_month=scenario.start_month,
            forecast=[MonthlyProjectionOut.from_domain(month) for month in scenario.forecast],
            metrics=ScenarioMetricsOut.from_domain(scenario.metrics),
            cost=CostBreakdownOut.from_domain(scenario.cost),
            warnings=scenario.warnings,
        )


class SimulateOut(BaseModel):
    profile_id: str
    item_name: str
    amount: int
    scenarios: list[ScenarioOut]

    @classmethod
    def from_domain(cls, simulation: SimulationResult) -> SimulateOut:
        return cls(
            profile_id=simulation.profile_id,
            item_name=simulation.item_name,
            amount=simulation.amount,
            scenarios=[ScenarioOut.from_domain(scenario) for scenario in simulation.scenarios],
        )


class ScoreBreakdownOut(BaseModel):
    cashflow_safety: float
    obligation_pressure: float
    goal_impact: float
    emergency_fund: float
    total_cost: float
    weighted_total: float

    @classmethod
    def from_domain(cls, breakdown: ScoreBreakdown) -> ScoreBreakdownOut:
        return cls(
            cashflow_safety=breakdown.cashflow_safety,
            obligation_pressure=breakdown.obligation_pressure,
            goal_impact=breakdown.goal_impact,
            emergency_fund=breakdown.emergency_fund,
            total_cost=breakdown.total_cost,
            weighted_total=breakdown.weighted_total,
        )


class ScenarioDecisionOut(BaseModel):
    scenario: ScenarioOut
    score: float
    recommended: bool
    blocked: bool
    reason_codes: list[str]
    score_breakdown: ScoreBreakdownOut

    @classmethod
    def from_domain(cls, decision: ScenarioDecision) -> ScenarioDecisionOut:
        if decision.score_breakdown is None:
            raise ValueError("score_breakdown is required")
        return cls(
            scenario=ScenarioOut.from_domain(decision.scenario),
            score=decision.score,
            recommended=decision.recommended,
            blocked=decision.blocked,
            reason_codes=decision.reason_codes,
            score_breakdown=ScoreBreakdownOut.from_domain(decision.score_breakdown),
        )


class RecommendOut(BaseModel):
    decision_id: str | None = None
    profile_id: str
    item_name: str
    amount: int
    best_scenario_id: str | None
    summary: str
    scenarios: list[ScenarioDecisionOut]
    advisories: list[str] = []
    min_confidence: float = 1.0
    low_confidence_obligations: list[str] = []

    @classmethod
    def from_domain(
        cls,
        recommendation: RecommendationResult,
        decision_id: str | None = None,
    ) -> RecommendOut:
        return cls(
            decision_id=decision_id,
            profile_id=recommendation.profile_id,
            item_name=recommendation.item_name,
            amount=recommendation.amount,
            best_scenario_id=recommendation.best_scenario_id,
            summary=recommendation.summary,
            scenarios=[
                ScenarioDecisionOut.from_domain(decision)
                for decision in recommendation.scenarios
            ],
            advisories=recommendation.advisories,
            min_confidence=recommendation.min_confidence,
            low_confidence_obligations=recommendation.low_confidence_obligations,
        )
