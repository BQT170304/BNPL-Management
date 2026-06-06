from __future__ import annotations

from fastapi import APIRouter, Depends

import app.dependencies as deps
from app.modules.ingestion.api.schemas import CifSeedOut, CifsOut
from app.modules.ingestion.application.service import IngestionService

router = APIRouter(tags=["ingestion"])


def _service() -> IngestionService:
    # Indirection so tests can monkeypatch deps.get_ingestion_service.
    return deps.get_ingestion_service()


@router.get("/ingestion/cifs", response_model=CifsOut)
async def list_cifs(service: IngestionService = Depends(_service)) -> CifsOut:
    return CifsOut(cifs=service.list_cifs())


@router.get("/ingestion/cif/{cif}/seed", response_model=CifSeedOut)
async def get_seed(
    cif: str, strategy: str = "latest",
    service: IngestionService = Depends(_service),
) -> CifSeedOut:
    seed = service.get_seed(cif, strategy=strategy)
    return CifSeedOut(cif=seed.cif, income=seed.income,
                      expense=seed.expense, debt_payment=seed.debt_payment)
