from __future__ import annotations

from datetime import datetime

from app.modules.ingestion.application.ports import CifSummary, TransactionRow
from app.modules.ingestion.application.service import IngestionService
from app.modules.portfolio.application.services import PortfolioService


class _SummarySource:
    def load(self, path: str) -> list[CifSummary]:
        return [
            CifSummary("100", "2025-01", 10_000_000, 4_000_000, 1_000_000),
            CifSummary("200", "2025-01", 10_000_000, 9_000_000, 1_000_000),
        ]


class _TransactionSource:
    def load(self, path: str) -> list[TransactionRow]:
        return [
            TransactionRow("100", "tra gop thang", datetime(2025, 1, 5), -1_000_000,
                           "Debt payment"),
            TransactionRow("100", "tra gop thang", datetime(2025, 2, 5), -1_000_000,
                           "Debt payment"),
            TransactionRow("200", "tra gop thang", datetime(2025, 1, 5), -4_000_000,
                           "Debt payment"),
            TransactionRow("200", "tra gop thang", datetime(2025, 2, 5), -4_000_000,
                           "Debt payment"),
        ]


def test_portfolio_summary_segments_customers():
    ingestion = IngestionService(
        _SummarySource(),
        "summary.csv",
        transaction_source=_TransactionSource(),
        transaction_csv_path="tx.csv",
    )
    summary = PortfolioService(ingestion).summarize()

    assert summary.total_customers == 2
    assert summary.evaluated_customers == 2
    assert summary.at_risk_count == 1
    assert summary.cross_sell_ready_count == 1
    assert summary.estimated_npl_avoided == int(summary.total_estimated_obligation * 0.15)
