from __future__ import annotations

import logging
import warnings
from typing import Protocol

from app.modules.forecasting.domain.history import MonthlyCashflowPoint


class BaseCashflowForecaster(Protocol):
    """Projects the *base* monthly net cashflow (income - expense - debt),
    before scenario obligations are layered on top."""

    def forecast_base(
        self,
        history: list[MonthlyCashflowPoint],
        current_base: int,
        periods: int,
    ) -> list[int]: ...


class FlatCashflowForecaster:
    """Deterministic baseline: repeats the current base cashflow every month.

    This reproduces the original forecast behaviour and is the safe default.
    """

    def forecast_base(
        self,
        history: list[MonthlyCashflowPoint],
        current_base: int,
        periods: int,
    ) -> list[int]:
        return [current_base] * periods


class ProphetCashflowForecaster:
    """Forecasts base net cashflow with Prophet using the CIF's monthly history.

    Falls back to the flat projection when there is too little history or when
    Prophet is unavailable / fails, so a forecast is always produced.
    """

    def __init__(self, min_points: int = 4) -> None:
        self._min_points = min_points
        self._fallback = FlatCashflowForecaster()

    def forecast_base(
        self,
        history: list[MonthlyCashflowPoint],
        current_base: int,
        periods: int,
    ) -> list[int]:
        if periods <= 0:
            return []
        if len(history) < self._min_points:
            return self._fallback.forecast_base(history, current_base, periods)
        try:
            return self._predict(history, periods)
        except Exception:  # pragma: no cover - any Prophet/runtime failure
            logging.getLogger(__name__).warning(
                "Prophet forecast failed; falling back to flat projection",
                exc_info=True,
            )
            return self._fallback.forecast_base(history, current_base, periods)

    def _predict(self, history: list[MonthlyCashflowPoint], periods: int) -> list[int]:
        import pandas as pd

        logging.getLogger("cmdstanpy").setLevel(logging.ERROR)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from prophet import Prophet

            frame = pd.DataFrame({
                "ds": pd.to_datetime([f"{point.month}-01" for point in history]),
                "y": [point.net_cashflow for point in history],
            })
            model = Prophet(
                weekly_seasonality=False,
                daily_seasonality=False,
                yearly_seasonality=len(history) >= 24,
            )
            model.fit(frame)
            future = model.make_future_dataframe(periods=periods, freq="MS")
            forecast = model.predict(future)
            predictions = forecast["yhat"].tail(periods).tolist()
        return [int(round(value)) for value in predictions]
