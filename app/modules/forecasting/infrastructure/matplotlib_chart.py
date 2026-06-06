from __future__ import annotations

import io
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

from app.modules.forecasting.domain.models import ForecastResult  # noqa: E402

_MILLION = 1_000_000.0


class MatplotlibChart:
    def render(self, result: ForecastResult) -> bytes:
        fig, ax = plt.subplots(figsize=(10, 5))

        # matplotlib accepts date objects on the x-axis at runtime; the stubs are
        # stricter than reality, so the date sequences are typed as Any.
        hist_x: list[Any] = [p.ds for p in result.history]
        hist_y = [p.y / _MILLION for p in result.history]
        ax.plot(hist_x, hist_y, color="#9ec5fe", linewidth=1.0, label="History")

        fc_x: list[Any] = [p.ds for p in result.forecast]
        fc_y = [p.yhat / _MILLION for p in result.forecast]
        fc_lo = [p.lower / _MILLION for p in result.forecast]
        fc_hi = [p.upper / _MILLION for p in result.forecast]
        ax.plot(fc_x, fc_y, color="#0d6efd", linewidth=1.5, label="Forecast")
        ax.fill_between(fc_x, fc_lo, fc_hi, color="#0d6efd", alpha=0.15)

        if result.history:
            divider: Any = result.history[-1].ds
            ax.axvline(divider, color="grey", linestyle="--", linewidth=0.8)

        ax.set_title(f"Dự báo dòng tiền — CIF {result.cif}")
        ax.set_ylabel("Net cashflow (triệu VND)")
        ax.legend(loc="best")
        fig.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=120)
        plt.close(fig)
        return buf.getvalue()
