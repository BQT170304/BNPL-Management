from __future__ import annotations

from datetime import timedelta
from statistics import pstdev

from app.modules.forecasting.domain.models import ForecastPoint, HistoryPoint


class NaiveForecaster:
    """Deterministic fallback: flat forecast at the recent mean with +/- 1 std band."""

    def forecast(self, series: list[HistoryPoint], horizon: int) -> list[ForecastPoint]:
        if not series:
            return []

        window = series[-min(30, len(series)):]
        values = [p.y for p in window]
        mu = sum(values) / len(values)
        sigma = pstdev(values) if len(values) > 1 else 0.0

        last_ds = series[-1].ds
        points: list[ForecastPoint] = []
        for step in range(1, horizon + 1):
            ds = last_ds + timedelta(days=step)
            points.append(ForecastPoint(ds=ds, yhat=mu, lower=mu - sigma, upper=mu + sigma))
        return points
