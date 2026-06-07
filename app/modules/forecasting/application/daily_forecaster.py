from __future__ import annotations

import logging
import warnings
from datetime import date, datetime, timedelta

from app.modules.forecasting.domain.daily import DailyForecastPoint, DailyForecastResult

MIN_POINTS = 14


def _fallback(
    profile_id: str,
    history: list[tuple[str, int]],
    days: int,
    starting_balance: int,
) -> DailyForecastResult:
    avg = round(sum(n for _, n in history) / len(history)) if history else 0
    last = (
        datetime.fromisoformat(history[-1][0]).date() if history else date.today()
    )
    points: list[DailyForecastPoint] = []
    balance = starting_balance
    for i in range(1, days + 1):
        d = last + timedelta(days=i)
        balance += avg
        points.append(DailyForecastPoint(d.isoformat(), avg, avg, avg, balance))
    min_bal = min((p.projected_balance for p in points), default=starting_balance)
    return DailyForecastResult(
        profile_id=profile_id, engine="fallback", history_days=len(history),
        days=days, starting_balance=starting_balance,
        min_projected_balance=min_bal, points=points,
    )


def forecast_daily(
    profile_id: str,
    history: list[tuple[str, int]],
    days: int,
    starting_balance: int,
) -> DailyForecastResult:
    """Daily net-cashflow forecast with Prophet (weekly seasonality), projecting
    a running balance. Falls back to a flat average when history is too short or
    Prophet is unavailable."""

    if days <= 0:
        days = 30
    if len(history) < MIN_POINTS:
        return _fallback(profile_id, history, days, starting_balance)
    try:
        import pandas as pd

        logging.getLogger("cmdstanpy").setLevel(logging.ERROR)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from prophet import Prophet

            frame = pd.DataFrame({
                "ds": pd.to_datetime([d for d, _ in history]),
                "y": [n for _, n in history],
            })
            model = Prophet(
                weekly_seasonality=True,
                daily_seasonality=False,
                yearly_seasonality=False,
            )
            model.fit(frame)
            future = model.make_future_dataframe(periods=days, freq="D")
            forecast = model.predict(future).tail(days)
        points: list[DailyForecastPoint] = []
        balance = starting_balance
        for _, row in forecast.iterrows():
            net = int(round(row["yhat"]))
            balance += net
            points.append(DailyForecastPoint(
                date=row["ds"].date().isoformat(),
                predicted_net=net,
                lower=int(round(row["yhat_lower"])),
                upper=int(round(row["yhat_upper"])),
                projected_balance=balance,
            ))
        min_bal = min((p.projected_balance for p in points), default=starting_balance)
        return DailyForecastResult(
            profile_id=profile_id, engine="prophet", history_days=len(history),
            days=days, starting_balance=starting_balance,
            min_projected_balance=min_bal, points=points,
        )
    except Exception:  # pragma: no cover
        logging.getLogger(__name__).warning("Prophet daily failed; fallback", exc_info=True)
        return _fallback(profile_id, history, days, starting_balance)
