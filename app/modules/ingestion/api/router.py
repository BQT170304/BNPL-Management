from __future__ import annotations

from fastapi import APIRouter, Depends

import app.dependencies as deps
from app.modules.consent.application.services import ConsentService
from app.modules.consent.domain.entities import ConsentScope
from app.modules.ingestion.api.schemas import (
    CifObligationSeedOut,
    CifObligationSeedsOut,
    CifSeedOut,
    CifsOut,
    SeededObligationsOut,
)
from app.modules.ingestion.application.service import IngestionService
from app.modules.obligations.api.schemas import ObligationOut
from app.modules.obligations.application.services import ObligationService

router = APIRouter(tags=["ingestion"])


def _service() -> IngestionService:
    # Indirection so tests can monkeypatch deps.get_ingestion_service.
    return deps.get_ingestion_service()


def _consent_service() -> ConsentService:
    # Indirection so tests can monkeypatch deps.get_consent_service.
    return deps.get_consent_service()


@router.get("/ingestion/cifs", response_model=CifsOut)
async def list_cifs(service: IngestionService = Depends(_service)) -> CifsOut:
    # Catalogue of CIF identifiers only (no banking data) so the user can
    # choose which CIF to authorise; the data reads below are consent-gated.
    return CifsOut(cifs=service.list_cifs())


@router.get("/ingestion/cif/{cif}/seed", response_model=CifSeedOut)
async def get_seed(
    cif: str,
    strategy: str = "latest",
    service: IngestionService = Depends(_service),
    consent: ConsentService = Depends(_consent_service),
) -> CifSeedOut:
    await consent.ensure(cif, ConsentScope.CIF_SUMMARY)
    seed = service.get_seed(cif, strategy=strategy)
    return CifSeedOut(cif=seed.cif, income=seed.income,
                      expense=seed.expense, debt_payment=seed.debt_payment)


@router.get("/ingestion/cif/{cif}/obligation-seeds", response_model=CifObligationSeedsOut)
async def get_obligation_seeds(
    cif: str,
    min_payments: int = 2,
    limit: int = 10,
    service: IngestionService = Depends(_service),
    consent: ConsentService = Depends(_consent_service),
) -> CifObligationSeedsOut:
    await consent.ensure(cif, ConsentScope.CIF_TRANSACTIONS)
    seeds = service.get_obligation_seeds(cif, min_payments=min_payments, limit=limit)
    return CifObligationSeedsOut(
        cif=cif,
        obligations=[CifObligationSeedOut.from_domain(seed) for seed in seeds],
    )


@router.post(
    "/profiles/{profile_id}/obligations/from-cif/{cif}",
    response_model=SeededObligationsOut,
)
async def seed_obligations_from_cif(
    profile_id: str,
    cif: str,
    min_payments: int = 2,
    limit: int = 10,
    ingestion: IngestionService = Depends(_service),
    obligations: ObligationService = Depends(deps.get_obligation_service),
    consent: ConsentService = Depends(_consent_service),
) -> SeededObligationsOut:
    granted = await consent.ensure(cif, ConsentScope.CIF_TRANSACTIONS)
    seeds = ingestion.get_obligation_seeds(cif, min_payments=min_payments, limit=limit)
    created = []
    for seed in seeds:
        created.append(await obligations.add(seed.to_obligation(profile_id)))
    await consent.link_cif(profile_id, cif, consent_id=granted.id)
    return SeededObligationsOut(
        profile_id=profile_id,
        cif=cif,
        obligations=[ObligationOut.from_domain(obligation) for obligation in created],
    )
