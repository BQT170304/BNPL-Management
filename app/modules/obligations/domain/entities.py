from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum


class ObligationType(str, Enum):
    BNPL = "BNPL"
    LOAN = "LOAN"
    CREDIT_CARD = "CREDIT_CARD"
    BILL = "BILL"
    SUBSCRIPTION = "SUBSCRIPTION"


class ObligationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CLOSED = "CLOSED"


@dataclass(frozen=True)
class Obligation:
    id: str
    profile_id: str
    type: ObligationType
    merchant: str
    category: str
    principal_amount: int
    monthly_payment: int
    due_day: int
    start_date: date
    end_date: date | None = None
    remaining_terms: int | None = None
    apr: float = 0.0
    status: ObligationStatus = ObligationStatus.ACTIVE
    confidence: float = 1.0
    verified_by: str | None = None
    verified_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("obligation id is required")
        if not self.profile_id:
            raise ValueError("profile_id is required")
        if self.principal_amount < 0:
            raise ValueError("principal_amount must be >= 0")
        if self.monthly_payment < 0:
            raise ValueError("monthly_payment must be >= 0")
        if not 1 <= self.due_day <= 31:
            raise ValueError("due_day must be between 1 and 31")
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        if self.remaining_terms is not None and self.remaining_terms < 0:
            raise ValueError("remaining_terms must be >= 0")
        if self.apr < 0:
            raise ValueError("apr must be >= 0")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")

    @property
    def verified(self) -> bool:
        return self.verified_by is not None
