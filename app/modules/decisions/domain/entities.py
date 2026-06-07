from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from app.modules.planning.domain.constraints import RecommendationResult


class OverrideAction(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    OVERRIDE = "OVERRIDE"


@dataclass(frozen=True)
class DecisionOverride:
    """A human (RM) decision recorded alongside the machine decision.

    The machine recommendation is never mutated; the override is stored next to
    it so the audit trail always shows both."""

    decision_id: str
    actor: str
    action: OverrideAction
    reason: str
    created_at: datetime
    scenario_id: str | None = None

    def __post_init__(self) -> None:
        if not self.actor:
            raise ValueError("actor is required")
        if not self.reason or not self.reason.strip():
            raise ValueError("reason is required")


@dataclass(frozen=True)
class DecisionTrace:
    id: str
    profile_id: str
    input_snapshot: dict[str, Any]
    recommendation: RecommendationResult
    model_version: str
    created_at: datetime
    override: DecisionOverride | None = None


@dataclass(frozen=True)
class DecisionExplanation:
    decision_id: str
    summary: str
    key_reasons: list[str]
    counterfactuals: list[str]
