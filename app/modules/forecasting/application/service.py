from __future__ import annotations

from app.modules.forecasting.application.ports import (
    ChartRenderer,
    Forecaster,
    TransactionSource,
)
from app.modules.forecasting.domain.daily_net import summarize
from app.modules.forecasting.domain.models import ForecastResult


class ForecastService:
    def __init__(
        self,
        source: TransactionSource,
        forecaster: Forecaster,
        renderer: ChartRenderer,
        horizon: int,
    ) -> None:
        self._source = source
        self._forecaster = forecaster
        self._renderer = renderer
        self._horizon = horizon
        self._results: dict[str, ForecastResult] = {}
        self._charts: dict[str, bytes] = {}

    def forecast(self, cif: str) -> ForecastResult:
        cached = self._results.get(cif)
        if cached is not None:
            return cached

        history = self._source.history(cif)
        forecast = self._forecaster.forecast(history, self._horizon)
        next_30, next_90 = summarize(forecast)
        result = ForecastResult(
            cif=cif,
            history=history,
            forecast=forecast,
            next_30_net=next_30,
            next_90_net=next_90,
        )
        self._results[cif] = result
        return result

    def chart(self, cif: str) -> bytes:
        cached = self._charts.get(cif)
        if cached is not None:
            return cached

        result = self.forecast(cif)
        png = self._renderer.render(result)
        self._charts[cif] = png
        return png
