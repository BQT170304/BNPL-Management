from __future__ import annotations

from typing import Protocol

from app.modules.forecasting.domain.models import (
    ForecastPoint,
    ForecastResult,
    HistoryPoint,
)


class Forecaster(Protocol):
    def forecast(self, series: list[HistoryPoint], horizon: int) -> list[ForecastPoint]:
        ...


class TransactionSource(Protocol):
    def history(self, cif: str) -> list[HistoryPoint]:
        """Return the daily net history for a CIF. Raises CifNotFound if no data."""
        ...


class ChartRenderer(Protocol):
    def render(self, result: ForecastResult) -> bytes:
        ...
