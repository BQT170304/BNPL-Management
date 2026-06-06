import pytest

from app.modules.ingestion.application.ports import CifSummary
from app.modules.ingestion.application.services import CifSeed, derive_seed


def test_derive_seed_from_latest_month():
    summaries = [
        CifSummary(cif="100", month="2025-01", income=10_000_000,
                   expense=4_000_000, debt_payment=1_000_000),
        CifSummary(cif="100", month="2025-02", income=12_000_000,
                   expense=5_000_000, debt_payment=2_000_000),
    ]
    seed = derive_seed("100", summaries, strategy="latest")
    assert seed == CifSeed(cif="100", income=12_000_000,
                           expense=5_000_000, debt_payment=2_000_000)


def test_derive_seed_average():
    summaries = [
        CifSummary("100", "2025-01", 10_000_000, 4_000_000, 1_000_000),
        CifSummary("100", "2025-02", 12_000_000, 6_000_000, 3_000_000),
    ]
    seed = derive_seed("100", summaries, strategy="average")
    assert seed == CifSeed("100", 11_000_000, 5_000_000, 2_000_000)


def test_derive_seed_unknown_cif_raises():
    summaries = [CifSummary("100", "2025-01", 10_000_000, 4_000_000, 1_000_000)]
    with pytest.raises(ValueError):
        derive_seed("999", summaries)
