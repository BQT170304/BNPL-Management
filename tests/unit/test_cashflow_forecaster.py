from __future__ import annotations

import pytest

from app.modules.forecasting.application.cashflow_forecaster import (
    FlatCashflowForecaster,
    ProphetCashflowForecaster,
)
from app.modules.forecasting.domain.history import MonthlyCashflowPoint


def _history(values: list[int], start_year: int = 2025) -> list[MonthlyCashflowPoint]:
    points = []
    month = 1
    year = start_year
    for value in values:
        points.append(MonthlyCashflowPoint(f"{year:04d}-{month:02d}", value))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return points


def test_flat_forecaster_repeats_current_base():
    forecaster = FlatCashflowForecaster()
    assert forecaster.forecast_base([], 5_000_000, 3) == [5_000_000, 5_000_000, 5_000_000]


def test_prophet_falls_back_when_history_too_short():
    forecaster = ProphetCashflowForecaster(min_points=4)
    result = forecaster.forecast_base(_history([1, 2, 3]), 5_000_000, 3)
    assert result == [5_000_000, 5_000_000, 5_000_000]


def test_prophet_predicts_trend_with_enough_history():
    pytest.importorskip("prophet")
    forecaster = ProphetCashflowForecaster(min_points=4)
    history = _history([
        5_000_000, 5_200_000, 5_400_000, 5_600_000,
        5_800_000, 6_000_000, 6_200_000, 6_400_000,
    ])
    result = forecaster.forecast_base(history, current_base=0, periods=3)
    assert len(result) == 3
    # used Prophet (not the flat fallback, which would be all zeros)
    assert any(value != 0 for value in result)
    # increasing history -> non-decreasing trend
    assert result[-1] >= result[0]
