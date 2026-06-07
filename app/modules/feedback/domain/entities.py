from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class RepaymentOutcome(str, Enum):
    PAID_ON_TIME = "PAID_ON_TIME"
    LATE = "LATE"
    MISSED = "MISSED"
    RESTRUCTURED = "RESTRUCTURED"
    DEFAULT = "DEFAULT"

    @property
    def is_good(self) -> bool:
        return self == RepaymentOutcome.PAID_ON_TIME

    @property
    def is_bad(self) -> bool:
        return self in (RepaymentOutcome.MISSED, RepaymentOutcome.DEFAULT)


@dataclass(frozen=True)
class Outcome:
    """The real repayment result of a decision, used to validate the model."""

    id: str
    decision_id: str
    profile_id: str
    outcome: RepaymentOutcome
    recorded_by: str
    recorded_at: datetime
    note: str | None = None

    def __post_init__(self) -> None:
        if not self.decision_id:
            raise ValueError("decision_id is required")
        if not self.recorded_by:
            raise ValueError("recorded_by is required")


@dataclass(frozen=True)
class FeedbackMetrics:
    total_outcomes: int
    approval_outcome_rate: float
    late_rate: float
    false_approve_rate: float
    false_reject_rate: float
    counts: dict[str, int]
