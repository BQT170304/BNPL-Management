from __future__ import annotations

from pydantic import BaseModel

from app.modules.analysis.domain.results import ProfileMetrics


class GoalMetricOut(BaseModel):
    goal_id: str
    name: str
    gap: int
    monthly_allocated: int
    gat: float
    delay: float
    grs: float
    months_remaining: int


class MetricsOut(BaseModel):
    ncf: int
    dti: float
    dti_band: str
    saving_rate: float
    efr: float
    pgrs: float
    goals: list[GoalMetricOut]
    flags: list[str]

    @classmethod
    def from_domain(cls, m: ProfileMetrics) -> MetricsOut:
        return cls(
            ncf=m.ncf, dti=m.dti, dti_band=m.dti_band.value,
            saving_rate=m.saving_rate, efr=m.efr, pgrs=m.pgrs,
            goals=[GoalMetricOut(**g.__dict__) for g in m.goals],
            flags=m.flags,
        )
