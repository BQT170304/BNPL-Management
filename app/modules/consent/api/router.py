from __future__ import annotations

from fastapi import APIRouter, Depends, status

import app.dependencies as deps
from app.modules.consent.api.schemas import (
    CifMappingOut,
    ConsentIn,
    ConsentOut,
    ConsentsOut,
)
from app.modules.consent.application.services import ConsentService
from app.modules.consent.domain.entities import ConsentScope

router = APIRouter(tags=["consent"])


def _service() -> ConsentService:
    # Indirection so tests can monkeypatch deps.get_consent_service.
    return deps.get_consent_service()


@router.post("/consents", response_model=ConsentOut, status_code=status.HTTP_201_CREATED)
async def grant_consent(
    body: ConsentIn,
    service: ConsentService = Depends(_service),
) -> ConsentOut:
    consent = await service.grant(
        cif=body.cif,
        scopes=[ConsentScope(scope) for scope in body.scopes],
        granted_by=body.granted_by,
        subject=body.subject,
        ttl_days=body.ttl_days,
    )
    return ConsentOut.from_domain(consent, service.now())


@router.get("/consents/{consent_id}", response_model=ConsentOut)
async def get_consent(
    consent_id: str,
    service: ConsentService = Depends(_service),
) -> ConsentOut:
    consent = await service.get(consent_id)
    return ConsentOut.from_domain(consent, service.now())


@router.post("/consents/{consent_id}/revoke", response_model=ConsentOut)
async def revoke_consent(
    consent_id: str,
    service: ConsentService = Depends(_service),
) -> ConsentOut:
    consent = await service.revoke(consent_id)
    return ConsentOut.from_domain(consent, service.now())


@router.get("/cifs/{cif}/consents", response_model=ConsentsOut)
async def list_cif_consents(
    cif: str,
    service: ConsentService = Depends(_service),
) -> ConsentsOut:
    consents = await service.list_for_cif(cif)
    now = service.now()
    return ConsentsOut(consents=[ConsentOut.from_domain(c, now) for c in consents])


@router.get("/profiles/{profile_id}/cifs", response_model=CifMappingOut)
async def profile_cifs(
    profile_id: str,
    service: ConsentService = Depends(_service),
) -> CifMappingOut:
    cifs = await service.cifs_for_profile(profile_id)
    return CifMappingOut(profile_id=profile_id, cifs=cifs)
