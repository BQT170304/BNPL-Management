from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from app.core.config import get_settings
from app.dependencies import get_analysis_service, get_forecast_service, get_repository
from app.modules.analysis.api.schemas import AlertOut, AlertsOut, MetricsOut
from app.modules.analysis.application.services import AnalysisService
from app.modules.analysis.domain.alerts import check_alerts
from app.modules.forecasting.application.services import ForecastService
from app.modules.forecasting.domain.warnings import forecast_alerts
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


@router.get("/profiles/{profile_id}/alerts", response_model=AlertsOut)
async def profile_alerts(
    profile_id: str,
    include_forecast: bool = False,
    months: int = Query(default=6, ge=1, le=24),
    repo: ProfileRepository = Depends(get_repository),
    analysis: AnalysisService = Depends(get_analysis_service),
    forecast: ForecastService = Depends(get_forecast_service),
) -> AlertsOut:
    profile = await repo.get(profile_id)
    alerts = [AlertOut.from_domain(alert) for alert in check_alerts(analysis.analyze(profile))]
    if include_forecast:
        result = await forecast.forecast(profile, months=months)
        projected = forecast_alerts(
            result,
            profile,
            safe_months=get_settings().efr_safe_months,
        )
        alerts.extend(AlertOut.from_forecast(alert) for alert in projected)
    return AlertsOut(alerts=alerts)
