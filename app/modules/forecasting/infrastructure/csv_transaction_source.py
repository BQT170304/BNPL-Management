from __future__ import annotations

import logging
import os
from datetime import date

import pandas as pd

from app.core.errors import CifNotFound
from app.modules.forecasting.domain.daily_net import build_daily_series
from app.modules.forecasting.domain.models import HistoryPoint

logger = logging.getLogger(__name__)


class CsvTransactionSource:
    """Daily-net history per CIF.

    Seeds from a CSV on disk when one exists, but never crashes if it is
    missing — the demo dataset is gitignored, so a fresh checkout has no file
    and relies entirely on uploaded transactions (see :meth:`ingest`).
    """

    def __init__(self, path: str | None) -> None:
        self._path = path
        self._by_cif: dict[str, list[tuple[date, float]]] | None = None

    def _load(self) -> None:
        self._by_cif = {}
        if not self._path or not os.path.exists(self._path):
            logger.info(
                "No transactions CSV at %s — forecasting relies on uploaded data",
                self._path,
            )
            return
        df = pd.read_csv(self._path, dtype={"CIF_NO": str})
        self._absorb_dataframe(df)

    def _absorb_dataframe(self, df: pd.DataFrame) -> None:
        """Merge a raw transaction DataFrame into the per-CIF daily-net index."""
        assert self._by_cif is not None
        df = df.copy()
        df["TRAN_DATE"] = pd.to_datetime(df["TRAN_DATE"])
        df["DAY"] = df["TRAN_DATE"].dt.date
        grouped = df.groupby(["CIF_NO", "DAY"])["AMOUNT"].sum().reset_index()
        for _, row in grouped.iterrows():
            cif = str(row["CIF_NO"])
            self._by_cif.setdefault(cif, []).append((row["DAY"], float(row["AMOUNT"])))

    def ingest(self, cif: str, records: list[tuple[date, float]]) -> None:
        """Replace the history for a CIF with freshly uploaded transactions.

        Daily nets are recomputed from scratch so re-uploading a file for the
        same CIF overwrites stale data rather than double-counting it.
        """
        if self._by_cif is None:
            self._load()
        assert self._by_cif is not None

        totals: dict[date, float] = {}
        for day, amount in records:
            totals[day] = totals.get(day, 0.0) + amount
        self._by_cif[str(cif)] = sorted(totals.items())

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
