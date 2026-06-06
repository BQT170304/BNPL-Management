from __future__ import annotations

from fastapi import APIRouter, Depends

import app.dependencies as deps
from app.modules.analysis.api.schemas import AlertOut, AlertsOut, MetricsOut
from app.modules.analysis.application.services import AnalysisService
from app.modules.analysis.domain.alerts import check_alerts
from app.modules.profiles.application.ports import ProfileRepository

router = APIRouter(tags=["analysis"])


def _repo() -> ProfileRepository:
    return deps.get_repository()


def _analysis() -> AnalysisService:
    return deps.get_analysis_service()


@router.get("/profiles/{profile_id}/alerts", response_model=AlertsOut)
async def get_alerts(
    profile_id: str,
    repo: ProfileRepository = Depends(_repo),
    analysis: AnalysisService = Depends(_analysis),
) -> AlertsOut:
    """Return financial health alerts for a profile."""
    profile = await repo.get(profile_id)
    metrics = analysis.analyze(profile)
    alerts = check_alerts(metrics)
    return AlertsOut(
        profile_id=profile_id,
        alerts=[
            AlertOut(
                code=a.code, level=a.level.value,
                message=a.message, recommendation=a.recommendation,
                affected_value=a.affected_value,
            )
            for a in alerts
        ],
        has_critical=any(a.level.value == "CRITICAL" for a in alerts),
    )
