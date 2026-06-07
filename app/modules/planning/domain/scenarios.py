from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.forecasting.domain.projection import MonthlyProjection
from app.modules.planning.domain.cost import CostBreakdown


@dataclass(frozen=True)
class ScenarioMetrics:
    min_balance: int
    max_dti: float
    efr_after: float
    goal_delay_months: float


@dataclass(frozen=True)
class ScenarioResult:
    scenario_id: str
    label: str
    upfront_payment: int
    monthly_payment: int
    duration_months: int | None
    start_month: str | None
    forecast: list[MonthlyProjection]
    metrics: ScenarioMetrics
    cost: CostBreakdown
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SimulationResult:
    profile_id: str
    item_name: str
    amount: int
    scenarios: list[ScenarioResult]
