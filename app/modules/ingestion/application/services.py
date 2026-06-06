from __future__ import annotations

from dataclasses import dataclass

from app.modules.ingestion.application.ports import CifSummary


@dataclass(frozen=True)
class CifSeed:
    cif: str
    income: int
    expense: int
    debt_payment: int


def derive_seed(cif: str, summaries: list[CifSummary], strategy: str = "latest") -> CifSeed:
    rows = sorted((s for s in summaries if s.cif == cif), key=lambda s: s.month)
    if not rows:
        raise ValueError(f"no summary rows for cif {cif}")
    if strategy == "average":
        n = len(rows)
        return CifSeed(
            cif=cif,
            income=sum(r.income for r in rows) // n,
            expense=sum(r.expense for r in rows) // n,
            debt_payment=sum(r.debt_payment for r in rows) // n,
        )
    latest = rows[-1]
    return CifSeed(cif, latest.income, latest.expense, latest.debt_payment)
