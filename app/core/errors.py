from __future__ import annotations


class DomainError(Exception):
    """Base for domain errors."""


class ProfileNotFound(DomainError):
    def __init__(self, profile_id: str) -> None:
        super().__init__(f"Profile not found: {profile_id}")
        self.profile_id = profile_id


class GoalNotFound(DomainError):
    def __init__(self, goal_id: str) -> None:
        super().__init__(f"Goal not found: {goal_id}")
        self.goal_id = goal_id


class ObligationNotFound(DomainError):
    def __init__(self, obligation_id: str) -> None:
        super().__init__(f"Obligation not found: {obligation_id}")
        self.obligation_id = obligation_id


class DecisionNotFound(DomainError):
    def __init__(self, decision_id: str) -> None:
        super().__init__(f"Decision not found: {decision_id}")
        self.decision_id = decision_id


class CifNotFound(DomainError):
    def __init__(self, cif: str) -> None:
        super().__init__(f"CIF not found: {cif}")
        self.cif = cif


class ConsentNotFound(DomainError):
    def __init__(self, consent_id: str) -> None:
        super().__init__(f"Consent not found: {consent_id}")
        self.consent_id = consent_id


class ConsentRequired(DomainError):
    """Raised when CIF data is accessed without an active consent."""

    def __init__(self, cif: str, scope: str) -> None:
        super().__init__(f"Consent required for CIF {cif} scope {scope}")
        self.cif = cif
        self.scope = scope


class InvalidInput(DomainError):
    pass


class InvalidCredentials(DomainError):
    def __init__(self, message: str = "Invalid username or password") -> None:
        super().__init__(message)


class Unauthorized(DomainError):
    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(message)
