from __future__ import annotations

import logging
import warnings

from app.modules.forecasting.domain.models import ForecastPoint, HistoryPoint


class ProphetForecaster:
    """Prophet-backed forecaster. Imports prophet lazily so collection never breaks."""

    def forecast(self, series: list[HistoryPoint], horizon: int) -> list[ForecastPoint]:
        if not series:
            return []

        # Silence cmdstanpy/prophet logging + warnings like the reference script.
        logging.getLogger("cmdstanpy").setLevel(logging.ERROR)
        logging.getLogger("prophet").setLevel(logging.ERROR)
        warnings.simplefilter("ignore")

        import pandas as pd
        from prophet import Prophet

        df = pd.DataFrame(
            {"ds": [p.ds for p in series], "y": [p.y for p in series]}
        )

        m = Prophet(
            weekly_seasonality=True,
            yearly_seasonality=False,
            daily_seasonality=False,
            seasonality_mode="additive",
            changepoint_prior_scale=0.05,
            interval_width=0.8,
        )
        m.add_seasonality(name="monthly", period=30.5, fourier_order=5)
        m.fit(df)

        future = m.make_future_dataframe(periods=horizon, freq="D")
        forecast = m.predict(future)

        last_history_ds = series[-1].ds
        rows = forecast[forecast["ds"].dt.date > last_history_ds]
        return [
            ForecastPoint(
                ds=row.ds.date(),
                yhat=float(row.yhat),
                lower=float(row.yhat_lower),
                upper=float(row.yhat_upper),
            )
            for row in rows.itertuples(index=False)
        ]
