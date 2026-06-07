from __future__ import annotations

from pydantic import BaseModel

from app.modules.analysis.domain.alerts import FinancialAlert
from app.modules.analysis.domain.results import ProfileMetrics
from app.modules.forecasting.domain.warnings import ForecastAlert


class AlertOut(BaseModel):
    code: str
    level: str
    message: str
    recommendation: str
    affected_value: float | None = None


class AlertsOut(BaseModel):
    profile_id: str
    alerts: list[AlertOut]
    has_critical: bool


class GoalMetricOut(BaseModel):
    goal_id: str
    name: str
    gap: int
    monthly_allocated: int
    gat: float
    delay: float
    grs: float
    months_remaining: int


class AdviceOut(BaseModel):
    advice: str
    scorer_used: str   # "llm" | "template"


class MetricsOut(BaseModel):
    ncf: int
    dti: float
    dti_band: str
    saving_rate: float
    efr: float
    pgrs: float
    goals: list[GoalMetricOut]
    flags: list[str]
    overall_health_score: int = 0
    metric_statuses: dict[str, str] = {}

    @classmethod
    def from_domain(cls, m: ProfileMetrics) -> "MetricsOut":
        return cls(
            ncf=m.ncf, dti=m.dti, dti_band=m.dti_band.value,
            saving_rate=m.saving_rate, efr=m.efr, pgrs=m.pgrs,
            goals=[GoalMetricOut(**g.__dict__) for g in m.goals],
            flags=m.flags,
            overall_health_score=m.overall_health_score,
            metric_statuses=m.metric_statuses,
        )


class AlertOut(BaseModel):
    code: str
    level: str
    message: str
    recommendation: str
    month: str | None = None

    @classmethod
    def from_domain(cls, alert: FinancialAlert) -> AlertOut:
        return cls(
            code=alert.code,
            level=alert.level.value,
            message=alert.message,
            recommendation=alert.recommendation,
            month=None,
        )

    @classmethod
    def from_forecast(cls, alert: ForecastAlert) -> AlertOut:
        return cls(
            code=alert.code,
            level=alert.level.value,
            message=alert.message,
            recommendation=alert.recommendation,
            month=alert.month,
        )


class AlertsOut(BaseModel):
    alerts: list[AlertOut]
