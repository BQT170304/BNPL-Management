from __future__ import annotations

from datetime import date

import pandas as pd

from app.core.errors import CifNotFound
from app.modules.forecasting.domain.daily_net import build_daily_series
from app.modules.forecasting.domain.models import HistoryPoint


class CsvTransactionSource:
    def __init__(self, path: str) -> None:
        self._path = path
        self._by_cif: dict[str, list[tuple[date, float]]] | None = None
        self._min: date | None = None
        self._max: date | None = None

    def _load(self) -> None:
        df = pd.read_csv(self._path, dtype={"CIF_NO": str})
        df["TRAN_DATE"] = pd.to_datetime(df["TRAN_DATE"])
        df["DAY"] = df["TRAN_DATE"].dt.date
        grouped = df.groupby(["CIF_NO", "DAY"])["AMOUNT"].sum().reset_index()

        by_cif: dict[str, list[tuple[date, float]]] = {}
        for _, row in grouped.iterrows():
            by_cif.setdefault(row["CIF_NO"], []).append((row["DAY"], float(row["AMOUNT"])))

        self._by_cif = by_cif
        all_days = grouped["DAY"]
        self._min = all_days.min()
        self._max = all_days.max()

    def history(self, cif: str) -> list[HistoryPoint]:
        if self._by_cif is None:
            self._load()
        assert self._by_cif is not None

        records = self._by_cif.get(cif)
        if records is None:
            raise CifNotFound(cif)
        # Use per-CIF date range so trailing zeros don't corrupt the forecast window.
        cif_min = min(day for day, _ in records)
        cif_max = max(day for day, _ in records)
        return build_daily_series(records, cif_min, cif_max)
