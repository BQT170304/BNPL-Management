from __future__ import annotations

from pydantic import BaseModel

from app.modules.ingestion.application.service import CifObligationSeed
from app.modules.obligations.api.schemas import ObligationOut


class CifsOut(BaseModel):
    cifs: list[str]


class CifSeedOut(BaseModel):
    cif: str
    income: int
    expense: int
    debt_payment: int


class CifObligationSeedOut(BaseModel):
    source_key: str
    type: str
    merchant: str
    category: str
    principal_amount: int
    monthly_payment: int
    due_day: int
    start_date: str
    end_date: str
    remaining_terms: int
    apr: float
    status: str
    confidence: float
    evidence_count: int
    active_months: int
    total_paid: int

    @classmethod
    def from_domain(cls, seed: CifObligationSeed) -> CifObligationSeedOut:
        return cls(
            source_key=seed.source_key,
            type=seed.type.value,
            merchant=seed.merchant,
            category=seed.category,
            principal_amount=seed.principal_amount,
            monthly_payment=seed.monthly_payment,
            due_day=seed.due_day,
            start_date=seed.start_date.isoformat(),
            end_date=seed.end_date.isoformat(),
            remaining_terms=seed.remaining_terms,
            apr=seed.apr,
            status=seed.status.value,
            confidence=seed.confidence,
            evidence_count=seed.evidence_count,
            active_months=seed.active_months,
            total_paid=seed.total_paid,
        )


class CifObligationSeedsOut(BaseModel):
    cif: str
    obligations: list[CifObligationSeedOut]


class SeededObligationsOut(BaseModel):
    profile_id: str
    cif: str
    obligations: list[ObligationOut]
