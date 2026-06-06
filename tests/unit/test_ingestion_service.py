import pytest

from app.core.errors import CifNotFound
from app.modules.ingestion.application.ports import CifSummary
from app.modules.ingestion.application.service import IngestionService


class _StubSource:
    def __init__(self, rows: list[CifSummary]):
        self._rows = rows
        self.load_calls = 0

    def load(self, path: str) -> list[CifSummary]:
        self.load_calls += 1
        return self._rows


def _rows() -> list[CifSummary]:
    return [
        CifSummary("100", "2025-01", 10_000_000, 4_000_000, 1_000_000),
        CifSummary("100", "2025-02", 12_000_000, 5_000_000, 2_000_000),
        CifSummary("200", "2025-01", 20_000_000, 8_000_000, 3_000_000),
    ]


def test_list_cifs_returns_sorted_distinct():
    svc = IngestionService(_StubSource(_rows()), csv_path="x.csv")
    assert svc.list_cifs() == ["100", "200"]


def test_get_seed_latest():
    svc = IngestionService(_StubSource(_rows()), csv_path="x.csv")
    seed = svc.get_seed("100", strategy="latest")
    assert (seed.income, seed.expense, seed.debt_payment) == (12_000_000, 5_000_000, 2_000_000)


def test_get_seed_unknown_cif_raises_cifnotfound():
    svc = IngestionService(_StubSource(_rows()), csv_path="x.csv")
    with pytest.raises(CifNotFound):
        svc.get_seed("999")


def test_summaries_loaded_once_and_cached():
    source = _StubSource(_rows())
    svc = IngestionService(source, csv_path="x.csv")
    svc.list_cifs()
    svc.get_seed("100")
    assert source.load_calls == 1
