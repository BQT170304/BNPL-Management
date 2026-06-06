from __future__ import annotations

from app.core.errors import CifNotFound
from app.modules.ingestion.application.ports import CifSummary, SummarySource
from app.modules.ingestion.application.services import CifSeed, derive_seed


class IngestionService:
    """Loads the summary CSV once and serves CIF lists and derived seeds."""

    def __init__(self, source: SummarySource, csv_path: str) -> None:
        self._source = source
        self._csv_path = csv_path
        self._rows: list[CifSummary] | None = None

    def _summaries(self) -> list[CifSummary]:
        if self._rows is None:
            self._rows = self._source.load(self._csv_path)
        return self._rows

    def list_cifs(self) -> list[str]:
        return sorted({r.cif for r in self._summaries()})

    def get_seed(self, cif: str, strategy: str = "latest") -> CifSeed:
        rows = self._summaries()
        if not any(r.cif == cif for r in rows):
            raise CifNotFound(cif)
        return derive_seed(cif, rows, strategy=strategy)
