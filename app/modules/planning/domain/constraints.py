from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.planning.domain.scenarios import ScenarioResult, SimulationResult


@dataclass(frozen=True)
class ScoreBreakdown:
    cashflow_safety: float
    obligation_pressure: float
    goal_impact: float
    emergency_fund: float
    total_cost: float

    @property
    def weighted_total(self) -> float:
        return round(
            self.cashflow_safety * 0.35
            + self.obligation_pressure * 0.25
            + self.goal_impact * 0.20
            + self.emergency_fund * 0.10
            + self.total_cost * 0.10,
            1,
        )


@dataclass(frozen=True)
class ScenarioDecision:
    scenario: ScenarioResult
    score: float
    recommended: bool
    blocked: bool
    reason_codes: list[str] = field(default_factory=list)
    score_breakdown: ScoreBreakdown | None = None


@dataclass(frozen=True)
class RecommendationResult:
    profile_id: str
    item_name: str
    amount: int
    best_scenario_id: str | None
    summary: str
    scenarios: list[ScenarioDecision]
    simulation: SimulationResult
    advisories: list[str] = field(default_factory=list)
    min_confidence: float = 1.0
    low_confidence_obligations: list[str] = field(default_factory=list)
