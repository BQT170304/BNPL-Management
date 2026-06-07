from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.modules.decisions.domain.entities import (
    DecisionExplanation,
    DecisionOverride,
    DecisionTrace,
)
from app.modules.planning.api.schemas import RecommendOut

OverrideActionValue = Literal["APPROVE", "REJECT", "OVERRIDE"]


class OverrideIn(BaseModel):
    actor: str = Field(min_length=1)
    action: OverrideActionValue
    reason: str = Field(min_length=1)
    scenario_id: str | None = None


class DecisionOverrideOut(BaseModel):
    decision_id: str
    actor: str
    action: str
    reason: str
    scenario_id: str | None
    created_at: datetime

    @classmethod
    def from_domain(cls, override: DecisionOverride) -> DecisionOverrideOut:
        return cls(
            decision_id=override.decision_id,
            actor=override.actor,
            action=override.action.value,
            reason=override.reason,
            scenario_id=override.scenario_id,
            created_at=override.created_at,
        )


class DecisionTraceOut(BaseModel):
    decision_id: str
    profile_id: str
    input_snapshot: dict[str, Any]
    recommendation: RecommendOut
    model_version: str
    created_at: datetime
    override: DecisionOverrideOut | None = None

    @classmethod
    def from_domain(cls, trace: DecisionTrace) -> DecisionTraceOut:
        return cls(
            decision_id=trace.id,
            profile_id=trace.profile_id,
            input_snapshot=trace.input_snapshot,
            recommendation=RecommendOut.from_domain(trace.recommendation, decision_id=trace.id),
            model_version=trace.model_version,
            created_at=trace.created_at,
            override=(
                DecisionOverrideOut.from_domain(trace.override)
                if trace.override is not None
                else None
            ),
        )


class DecisionExplanationOut(BaseModel):
    decision_id: str
    summary: str
    key_reasons: list[str]
    counterfactuals: list[str]

    @classmethod
    def from_domain(cls, explanation: DecisionExplanation) -> DecisionExplanationOut:
        return cls(
            decision_id=explanation.decision_id,
            summary=explanation.summary,
            key_reasons=explanation.key_reasons,
            counterfactuals=explanation.counterfactuals,
        )
