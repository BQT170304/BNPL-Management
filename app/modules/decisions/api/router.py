from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_decision_service
from app.modules.decisions.api.schemas import (
    DecisionExplanationOut,
    DecisionTraceOut,
    OverrideIn,
)
from app.modules.decisions.application.services import DecisionService

router = APIRouter(tags=["decisions"])


@router.get("/decisions/{decision_id}", response_model=DecisionTraceOut)
async def get_decision(
    decision_id: str,
    service: DecisionService = Depends(get_decision_service),
) -> DecisionTraceOut:
    return DecisionTraceOut.from_domain(await service.get(decision_id))


@router.post("/decisions/{decision_id}/explain", response_model=DecisionExplanationOut)
async def explain_decision(
    decision_id: str,
    service: DecisionService = Depends(get_decision_service),
) -> DecisionExplanationOut:
    return DecisionExplanationOut.from_domain(await service.explain(decision_id))


@router.post("/decisions/{decision_id}/override", response_model=DecisionTraceOut)
async def override_decision(
    decision_id: str,
    body: OverrideIn,
    service: DecisionService = Depends(get_decision_service),
) -> DecisionTraceOut:
    trace = await service.override(
        decision_id,
        actor=body.actor,
        action=body.action,
        reason=body.reason,
        scenario_id=body.scenario_id,
    )
    return DecisionTraceOut.from_domain(trace)
