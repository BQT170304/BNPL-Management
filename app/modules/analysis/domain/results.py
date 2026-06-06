# app/modules/analysis/domain/results.py
from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.analysis.domain.thresholds import DtiBand


@dataclass
class GoalMetric:
    goal_id: str
    name: str
    gap: int
    monthly_allocated: int
    gat: float
    delay: float
    grs: float
    months_remaining: int


@dataclass
class ProfileMetrics:
    ncf: int
    dti: float
    dti_band: DtiBand
    saving_rate: float
    efr: float
    pgrs: float
    goals: list[GoalMetric] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    overall_health_score: int = 0
    metric_statuses: dict = field(default_factory=dict)
