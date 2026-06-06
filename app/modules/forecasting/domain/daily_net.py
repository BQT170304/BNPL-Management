from __future__ import annotations

from datetime import date, timedelta

from app.modules.forecasting.domain.models import ForecastPoint, HistoryPoint


def build_daily_series(
    records: list[tuple[date, float]], start: date, end: date
) -> list[HistoryPoint]:
    """Sum amounts per day, then emit every day from start..end inclusive (gaps filled 0)."""
    totals: dict[date, float] = {}
    for day, amount in records:
        totals[day] = totals.get(day, 0.0) + amount

    series: list[HistoryPoint] = []
    current = start
    while current <= end:
        series.append(HistoryPoint(ds=current, y=totals.get(current, 0.0)))
        current = current + timedelta(days=1)
    return series


def summarize(forecast: list[ForecastPoint]) -> tuple[float, float]:
    """Return (sum of first 30 yhat, sum of first 90 yhat)."""
    n = len(forecast)
    next_30 = sum(p.yhat for p in forecast[: min(30, n)])
    next_90 = sum(p.yhat for p in forecast[: min(90, n)])
    return next_30, next_90
