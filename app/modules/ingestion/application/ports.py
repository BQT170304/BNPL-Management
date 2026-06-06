from __future__ import annotations

from dataclasses import dataclass
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
