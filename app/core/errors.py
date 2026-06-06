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


class CifNotFound(DomainError):
    def __init__(self, cif: str) -> None:
        super().__init__(f"CIF not found: {cif}")
        self.cif = cif


class InvalidInput(DomainError):
    pass


class InvalidCredentials(DomainError):
    def __init__(self, message: str = "Invalid username or password") -> None:
        super().__init__(message)


class Unauthorized(DomainError):
    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(message)
