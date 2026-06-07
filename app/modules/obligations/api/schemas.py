from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.modules.obligations.domain.entities import (
    Obligation,
    ObligationStatus,
    ObligationType,
)

ObligationTypeValue = Literal["BNPL", "LOAN", "CREDIT_CARD", "BILL", "SUBSCRIPTION"]
ObligationStatusValue = Literal["ACTIVE", "PAUSED", "CLOSED"]


class ObligationIn(BaseModel):
    id: str = Field(min_length=1)
    type: ObligationTypeValue
    merchant: str = Field(min_length=1)
    category: str = Field(min_length=1)
    principal_amount: int = Field(ge=0)
    monthly_payment: int = Field(ge=0)
    due_day: int = Field(ge=1, le=31)
    start_date: date
    end_date: date | None = None
    remaining_terms: int | None = Field(default=None, ge=0)
    apr: float = Field(default=0.0, ge=0)
    status: ObligationStatusValue = "ACTIVE"
    confidence: float = Field(default=1.0, ge=0, le=1)

    @model_validator(mode="after")
    def validate_dates(self) -> ObligationIn:
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self

    def to_domain(self, profile_id: str) -> Obligation:
        return Obligation(
            id=self.id,
            profile_id=profile_id,
            type=ObligationType(self.type),
            merchant=self.merchant,
            category=self.category,
            principal_amount=self.principal_amount,
            monthly_payment=self.monthly_payment,
            due_day=self.due_day,
            start_date=self.start_date,
            end_date=self.end_date,
            remaining_terms=self.remaining_terms,
            apr=self.apr,
            status=ObligationStatus(self.status),
            confidence=self.confidence,
        )


class ObligationVerifyIn(BaseModel):
    verified_by: str = Field(min_length=1)


class ObligationOut(BaseModel):
    id: str
    profile_id: str
    type: str
    merchant: str
    category: str
    principal_amount: int
    monthly_payment: int
    due_day: int
    start_date: date
    end_date: date | None
    remaining_terms: int | None
    apr: float
    status: str
    confidence: float
    verified: bool
    verified_by: str | None
    verified_at: datetime | None

    @classmethod
    def from_domain(cls, obligation: Obligation) -> ObligationOut:
        return cls(
            id=obligation.id,
            profile_id=obligation.profile_id,
            type=obligation.type.value,
            merchant=obligation.merchant,
            category=obligation.category,
            principal_amount=obligation.principal_amount,
            monthly_payment=obligation.monthly_payment,
            due_day=obligation.due_day,
            start_date=obligation.start_date,
            end_date=obligation.end_date,
            remaining_terms=obligation.remaining_terms,
            apr=obligation.apr,
            status=obligation.status.value,
            confidence=obligation.confidence,
            verified=obligation.verified,
            verified_by=obligation.verified_by,
            verified_at=obligation.verified_at,
        )


class ObligationsOut(BaseModel):
    obligations: list[ObligationOut]
