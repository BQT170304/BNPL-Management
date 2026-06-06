from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.dependencies import get_analysis_service, get_repository
from app.modules.analysis.api.schemas import MetricsOut
from app.modules.analysis.application.services import AnalysisService
from app.modules.profiles.api.mappers import to_domain
from app.modules.profiles.api.schemas import ProfileIn
from app.modules.profiles.application.ports import ProfileRepository

router = APIRouter(tags=["profiles"])


@router.post("/profiles", status_code=status.HTTP_201_CREATED)
async def create_profile(
    body: ProfileIn, repo: ProfileRepository = Depends(get_repository)
) -> dict[str, str]:
    await repo.add(to_domain(body))
    return {"id": body.id}


@router.get("/profiles/{profile_id}/analysis", response_model=MetricsOut)
async def analyze_profile(
    profile_id: str,
    repo: ProfileRepository = Depends(get_repository),
    analysis: AnalysisService = Depends(get_analysis_service),
) -> MetricsOut:
    profile = await repo.get(profile_id)
    return MetricsOut.from_domain(analysis.analyze(profile))
