from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_daily_forecast_service, get_forecast_service, get_repository
from app.modules.forecasting.api.schemas import DailyForecastOut, ForecastOut
from app.modules.forecasting.application.daily_service import DailyForecastService
from app.modules.forecasting.application.services import ForecastService
from app.modules.profiles.application.ports import ProfileRepository

router = APIRouter(tags=["forecasting"])


@router.get("/profiles/{profile_id}/forecast", response_model=ForecastOut)
async def forecast_profile(
    profile_id: str,
    months: int = Query(default=6, ge=1, le=24),
    repo: ProfileRepository = Depends(get_repository),
    service: ForecastService = Depends(get_forecast_service),
) -> ForecastOut:
    profile = await repo.get(profile_id)
    return ForecastOut.from_domain(await service.forecast(profile, months=months))


@router.get("/profiles/{profile_id}/forecast/daily", response_model=DailyForecastOut)
async def forecast_profile_daily(
    profile_id: str,
    days: int = Query(default=90, ge=7, le=180),
    repo: ProfileRepository = Depends(get_repository),
    service: DailyForecastService = Depends(get_daily_forecast_service),
) -> DailyForecastOut:
    profile = await repo.get(profile_id)
    return DailyForecastOut.from_domain(await service.forecast(profile, days=days))
