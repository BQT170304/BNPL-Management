from __future__ import annotations

from datetime import datetime

from app.modules.ingestion.application.ports import CifSummary, TransactionRow
from app.modules.ingestion.application.service import IngestionService


class _SummarySource:
    def load(self, path: str) -> list[CifSummary]:
        return [CifSummary("100", "2025-01", 10_000_000, 4_000_000, 1_000_000)]


class _TransactionSource:
    def load(self, path: str) -> list[TransactionRow]:
        return [
            TransactionRow("100", "tra gop thang", datetime(2025, 1, 5), -1_200_000,
                           "Debt payment"),
            TransactionRow("100", "tra gop thang", datetime(2025, 2, 5), -1_800_000,
                           "Debt payment"),
            TransactionRow("100", "thanh toan the tin dung", datetime(2025, 1, 20), -500_000,
                           "Debt payment"),
            TransactionRow("100", "tien dien", datetime(2025, 1, 15), -300_000, "Expense"),
            TransactionRow("200", "tra gop thang", datetime(2025, 1, 5), -9_000_000,
                           "Debt payment"),
        ]


def _service() -> IngestionService:
    return IngestionService(
        _SummarySource(),
        "summary.csv",
        transaction_source=_TransactionSource(),
        transaction_csv_path="transactions.csv",
    )


def test_get_obligation_seeds_derives_bnpl_from_debt_payments():
    seeds = _service().get_obligation_seeds("100", min_payments=2)

    assert len(seeds) == 1
    seed = seeds[0]
    assert seed.source_key == "auto_tra_gop_thang"
    assert seed.type.value == "BNPL"
    assert seed.monthly_payment == 1_500_000
    assert seed.principal_amount == 3_000_000
    assert seed.due_day == 5
    assert seed.evidence_count == 2
    assert seed.active_months == 2
    assert seed.confidence == 0.65


def test_get_obligation_seeds_respects_limit():
    seeds = _service().get_obligation_seeds("100", min_payments=1, limit=1)

    assert len(seeds) == 1
    assert seeds[0].source_key == "auto_tra_gop_thang"


def test_obligation_seed_converts_to_profile_obligation():
    seed = _service().get_obligation_seeds("100", min_payments=2)[0]

    obligation = seed.to_obligation("profile_1")

    assert obligation.id == "profile_1_auto_tra_gop_thang"
    assert obligation.profile_id == "profile_1"
    assert obligation.monthly_payment == 1_500_000
    assert obligation.confidence == 0.65
