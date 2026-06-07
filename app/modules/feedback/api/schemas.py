from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.modules.feedback.domain.entities import FeedbackMetrics, Outcome

RepaymentOutcomeValue = Literal[
    "PAID_ON_TIME", "LATE", "MISSED", "RESTRUCTURED", "DEFAULT"
]


class OutcomeIn(BaseModel):
    outcome: RepaymentOutcomeValue
    recorded_by: str = Field(min_length=1)
    note: str | None = None


class OutcomeOut(BaseModel):
    id: str
    decision_id: str
    profile_id: str
    outcome: str
    recorded_by: str
    recorded_at: datetime
    note: str | None

    @classmethod
    def from_domain(cls, outcome: Outcome) -> OutcomeOut:
        return cls(
            id=outcome.id,
            decision_id=outcome.decision_id,
            profile_id=outcome.profile_id,
            outcome=outcome.outcome.value,
            recorded_by=outcome.recorded_by,
            recorded_at=outcome.recorded_at,
            note=outcome.note,
        )


class OutcomesOut(BaseModel):
    outcomes: list[OutcomeOut]


class FeedbackMetricsOut(BaseModel):
    total_outcomes: int
    approval_outcome_rate: float
    late_rate: float
    false_approve_rate: float
    false_reject_rate: float
    counts: dict[str, int]

    @classmethod
    def from_domain(cls, metrics: FeedbackMetrics) -> FeedbackMetricsOut:
        return cls(
            total_outcomes=metrics.total_outcomes,
            approval_outcome_rate=metrics.approval_outcome_rate,
            late_rate=metrics.late_rate,
            false_approve_rate=metrics.false_approve_rate,
            false_reject_rate=metrics.false_reject_rate,
            counts=metrics.counts,
        )


class DatasetOut(BaseModel):
    rows: list[dict[str, Any]]
