from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ConsentScope(str, Enum):
    """What slice of a CIF's banking data a consent authorises."""

    CIF_SUMMARY = "CIF_SUMMARY"
    CIF_TRANSACTIONS = "CIF_TRANSACTIONS"


class ConsentStatus(str, Enum):
    GRANTED = "GRANTED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True)
class Consent:
    """A data subject's authorisation to access a CIF's banking data.

    Consent is CIF-centric, not profile-centric: it records *who* authorised
    access (``granted_by``), *when* (``granted_at``), and *what* scope. This
    makes data access auditable instead of letting a CIF be used as an
    uncontrolled shortcut.
    """

    id: str
    cif: str
    scopes: tuple[ConsentScope, ...]
    granted_by: str
    granted_at: datetime
    subject: str | None = None
    expires_at: datetime | None = None
    revoked_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("consent id is required")
        if not self.cif:
            raise ValueError("cif is required")
        if not self.scopes:
            raise ValueError("at least one scope is required")
        if not self.granted_by:
            raise ValueError("granted_by is required")
        if self.expires_at is not None and self.expires_at <= self.granted_at:
            raise ValueError("expires_at must be after granted_at")

    def status_at(self, now: datetime) -> ConsentStatus:
        if self.revoked_at is not None:
            return ConsentStatus.REVOKED
        if self.expires_at is not None and now >= self.expires_at:
            return ConsentStatus.EXPIRED
        return ConsentStatus.GRANTED

    def is_active(self, now: datetime) -> bool:
        return self.status_at(now) == ConsentStatus.GRANTED

    def covers(self, scope: ConsentScope) -> bool:
        return scope in self.scopes


@dataclass(frozen=True)
class CifLink:
    """Maps a profile to a CIF. Many-to-many: one profile may link several
    CIFs, and one CIF may be linked from several profiles/contexts."""

    profile_id: str
    cif: str
    linked_at: datetime
    consent_id: str | None = None

    def __post_init__(self) -> None:
        if not self.profile_id:
            raise ValueError("profile_id is required")
        if not self.cif:
            raise ValueError("cif is required")


@dataclass(frozen=True)
class CifMapping:
    """Read model: the CIFs linked to a profile."""

    profile_id: str
    cifs: list[str] = field(default_factory=list)
