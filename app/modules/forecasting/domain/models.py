from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class HistoryPoint:
    ds: date
    y: float


@dataclass
class ForecastPoint:
    ds: date
    yhat: float
    lower: float
    upper: float


@dataclass
class ForecastResult:
    cif: str
    history: list[HistoryPoint]
    forecast: list[ForecastPoint]
    next_30_net: float
    next_90_net: float
