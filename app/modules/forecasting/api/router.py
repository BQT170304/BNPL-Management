from __future__ import annotations

from fastapi import APIRouter, Depends, Response

import app.dependencies as deps
from app.modules.forecasting.api.schemas import (
    ForecastOut,
    ForecastPointOut,
    HistoryPointOut,
)
from app.modules.forecasting.application.service import ForecastService

router = APIRouter(tags=["forecasting"])


def _service() -> ForecastService:
    # Indirection so tests can monkeypatch deps.get_forecast_service.
    return deps.get_forecast_service()


@router.get("/forecast/{cif}", response_model=ForecastOut)
async def get_forecast(
    cif: str, service: ForecastService = Depends(_service)
) -> ForecastOut:
    result = service.forecast(cif)
    return ForecastOut(
        cif=result.cif,
        next_30_net=result.next_30_net,
        next_90_net=result.next_90_net,
        history=[HistoryPointOut(ds=p.ds.isoformat(), y=p.y) for p in result.history],
        forecast=[
            ForecastPointOut(
                ds=p.ds.isoformat(), yhat=p.yhat, lower=p.lower, upper=p.upper
            )
            for p in result.forecast
        ],
    )


@router.get("/forecast/{cif}/chart.png")
async def get_forecast_chart(
    cif: str, service: ForecastService = Depends(_service)
) -> Response:
    return Response(content=service.chart(cif), media_type="image/png")
