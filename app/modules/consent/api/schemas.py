from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.modules.consent.domain.entities import Consent

ConsentScopeValue = Literal["CIF_SUMMARY", "CIF_TRANSACTIONS"]


class ConsentIn(BaseModel):
    cif: str = Field(min_length=1)
    scopes: list[ConsentScopeValue] = Field(min_length=1)
    granted_by: str = Field(min_length=1)
    subject: str | None = None
    ttl_days: int | None = Field(default=None, ge=1)


class ConsentOut(BaseModel):
    consent_id: str
    cif: str
    scopes: list[str]
    status: str
    granted_by: str
    subject: str | None
    granted_at: datetime
    expires_at: datetime | None
    revoked_at: datetime | None

    @classmethod
    def from_domain(cls, consent: Consent, now: datetime) -> ConsentOut:
        return cls(
            consent_id=consent.id,
            cif=consent.cif,
            scopes=[scope.value for scope in consent.scopes],
            status=consent.status_at(now).value,
            granted_by=consent.granted_by,
            subject=consent.subject,
            granted_at=consent.granted_at,
            expires_at=consent.expires_at,
            revoked_at=consent.revoked_at,
        )


class ConsentsOut(BaseModel):
    consents: list[ConsentOut]


class CifMappingOut(BaseModel):
    profile_id: str
    cifs: list[str]
