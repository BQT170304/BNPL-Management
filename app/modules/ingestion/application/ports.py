from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class CifSummary:
    cif: str
    month: str            # "YYYY-MM"
    income: int
    expense: int
    debt_payment: int


class SummarySource(Protocol):
    def load(self, path: str) -> list[CifSummary]:
        """Read summary_by_cif_month.csv into CifSummary rows."""
        ...


@dataclass(frozen=True)
class TransactionRow:
    cif: str
    note: str
    transacted_at: datetime
    amount: int
    category: str


class TransactionSource(Protocol):
    def load(self, path: str) -> list[TransactionRow]:
        """Read transactions_labeled.csv into transaction rows."""
        ...
