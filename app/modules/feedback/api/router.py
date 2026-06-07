from __future__ import annotations

from fastapi import APIRouter, Depends, status

import app.dependencies as deps
from app.modules.feedback.api.schemas import (
    DatasetOut,
    FeedbackMetricsOut,
    OutcomeIn,
    OutcomeOut,
    OutcomesOut,
)
from app.modules.feedback.application.services import FeedbackService
from app.modules.feedback.domain.entities import RepaymentOutcome

router = APIRouter(tags=["feedback"])


def _service() -> FeedbackService:
    # Indirection so tests can monkeypatch deps.get_feedback_service.
    return deps.get_feedback_service()


@router.post(
    "/decisions/{decision_id}/outcomes",
    response_model=OutcomeOut,
    status_code=status.HTTP_201_CREATED,
)
async def record_outcome(
    decision_id: str,
    body: OutcomeIn,
    service: FeedbackService = Depends(_service),
) -> OutcomeOut:
    outcome = await service.record(
        decision_id,
        RepaymentOutcome(body.outcome),
        recorded_by=body.recorded_by,
        note=body.note,
    )
    return OutcomeOut.from_domain(outcome)


@router.get("/feedback/outcomes", response_model=OutcomesOut)
async def list_outcomes(
    service: FeedbackService = Depends(_service),
) -> OutcomesOut:
    outcomes = await service.list_outcomes()
    return OutcomesOut(outcomes=[OutcomeOut.from_domain(o) for o in outcomes])


@router.get("/feedback/dataset", response_model=DatasetOut)
async def export_dataset(
    service: FeedbackService = Depends(_service),
) -> DatasetOut:
    return DatasetOut(rows=await service.export_dataset())


@router.get("/feedback/metrics", response_model=FeedbackMetricsOut)
async def feedback_metrics(
    service: FeedbackService = Depends(_service),
) -> FeedbackMetricsOut:
    return FeedbackMetricsOut.from_domain(await service.metrics())
