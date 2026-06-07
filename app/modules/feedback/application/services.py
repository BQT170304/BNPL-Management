from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.modules.decisions.application.ports import DecisionRepository
from app.modules.decisions.domain.entities import DecisionTrace, OverrideAction
from app.modules.feedback.application.ports import OutcomeRepository
from app.modules.feedback.domain.entities import (
    FeedbackMetrics,
    Outcome,
    RepaymentOutcome,
)


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _effective_approved(trace: DecisionTrace) -> bool:
    """The decision actually taken, honouring any human override."""

    override = trace.override
    if override is not None:
        if override.action == OverrideAction.APPROVE:
            return True
        if override.action == OverrideAction.REJECT:
            return False
        return override.scenario_id is not None
    return trace.recommendation.best_scenario_id is not None


class FeedbackService:
    def __init__(
        self,
        outcomes: OutcomeRepository,
        decisions: DecisionRepository,
        now: Callable[[], datetime] = _utcnow,
    ) -> None:
        self._outcomes = outcomes
        self._decisions = decisions
        self._now = now

    async def record(
        self,
        decision_id: str,
        outcome: RepaymentOutcome,
        recorded_by: str,
        note: str | None = None,
    ) -> Outcome:
        trace = await self._decisions.get(decision_id)  # raises if unknown
        record = Outcome(
            id=f"out_{uuid4().hex}",
            decision_id=decision_id,
            profile_id=trace.profile_id,
            outcome=outcome,
            recorded_by=recorded_by,
            recorded_at=self._now(),
            note=note,
        )
        await self._outcomes.upsert(record)
        return record

    async def list_outcomes(self) -> list[Outcome]:
        return await self._outcomes.list_all()

    async def export_dataset(self) -> list[dict[str, Any]]:
        """Decision features joined with the realised label, ready for offline
        training/validation of a supervised PD model (not trained here)."""

        rows: list[dict[str, Any]] = []
        for outcome in await self._outcomes.list_all():
            trace = await self._decisions.get(outcome.decision_id)
            recommendation = trace.recommendation
            rows.append({
                "decision_id": trace.id,
                "profile_id": trace.profile_id,
                "item_name": recommendation.item_name,
                "amount": recommendation.amount,
                "machine_best_scenario_id": recommendation.best_scenario_id,
                "machine_approved": recommendation.best_scenario_id is not None,
                "effective_approved": _effective_approved(trace),
                "min_confidence": recommendation.min_confidence,
                "model_version": trace.model_version,
                "outcome": outcome.outcome.value,
                "recorded_at": outcome.recorded_at.isoformat(),
            })
        return rows

    async def metrics(self) -> FeedbackMetrics:
        outcomes = await self._outcomes.list_all()
        total = len(outcomes)
        counts: dict[str, int] = {member.value: 0 for member in RepaymentOutcome}
        approved = 0
        approved_good = 0
        false_approve = 0
        rejected = 0
        false_reject = 0
        late = 0

        for outcome in outcomes:
            counts[outcome.outcome.value] += 1
            if outcome.outcome == RepaymentOutcome.LATE:
                late += 1
            trace = await self._decisions.get(outcome.decision_id)
            approved_flag = _effective_approved(trace)
            if approved_flag:
                approved += 1
                if outcome.outcome.is_good:
                    approved_good += 1
                if outcome.outcome.is_bad:
                    false_approve += 1
            else:
                rejected += 1
                if outcome.outcome.is_good:
                    false_reject += 1

        return FeedbackMetrics(
            total_outcomes=total,
            approval_outcome_rate=round(approved_good / approved, 3) if approved else 0.0,
            late_rate=round(late / total, 3) if total else 0.0,
            false_approve_rate=round(false_approve / approved, 3) if approved else 0.0,
            false_reject_rate=round(false_reject / rejected, 3) if rejected else 0.0,
            counts=counts,
        )
