from __future__ import annotations

from pydantic import BaseModel


class HistoryPointOut(BaseModel):
    ds: str
    y: float


class ForecastPointOut(BaseModel):
    ds: str
    yhat: float
    lower: float
    upper: float


class ForecastOut(BaseModel):
    cif: str
    next_30_net: float
    next_90_net: float
    history: list[HistoryPointOut]
    forecast: list[ForecastPointOut]
