from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from app.dependencies import get_obligation_service
from app.modules.obligations.api.schemas import (
    ObligationIn,
    ObligationOut,
    ObligationsOut,
    ObligationVerifyIn,
)
from app.modules.obligations.application.services import ObligationService

router = APIRouter(tags=["obligations"])


@router.post(
    "/profiles/{profile_id}/obligations",
    response_model=ObligationOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_obligation(
    profile_id: str,
    body: ObligationIn,
    service: ObligationService = Depends(get_obligation_service),
) -> ObligationOut:
    obligation = await service.add(body.to_domain(profile_id))
    return ObligationOut.from_domain(obligation)


@router.get("/profiles/{profile_id}/obligations", response_model=ObligationsOut)
async def list_obligations(
    profile_id: str,
    service: ObligationService = Depends(get_obligation_service),
) -> ObligationsOut:
    obligations = await service.list_by_profile(profile_id)
    return ObligationsOut(
        obligations=[ObligationOut.from_domain(obligation) for obligation in obligations]
    )


@router.delete(
    "/profiles/{profile_id}/obligations/{obligation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_obligation(
    profile_id: str,
    obligation_id: str,
    service: ObligationService = Depends(get_obligation_service),
) -> Response:
    await service.delete(profile_id, obligation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/obligations/{obligation_id}/verify", response_model=ObligationOut)
async def verify_obligation(
    obligation_id: str,
    body: ObligationVerifyIn,
    service: ObligationService = Depends(get_obligation_service),
) -> ObligationOut:
    obligation = await service.verify(obligation_id, body.verified_by)
    return ObligationOut.from_domain(obligation)
