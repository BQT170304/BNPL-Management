from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MonthlyCashflowPoint:
    """One historical month of base net cashflow (income - expense - debt)."""

    month: str  # "YYYY-MM"
    net_cashflow: int
