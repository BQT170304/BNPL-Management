from __future__ import annotations

from app.core.errors import InvalidCredentials
from app.modules.auth.domain.credentials import verify


class AuthService:
    def __init__(self, username: str, password: str, token: str, enabled: bool) -> None:
        self._username = username
        self._password = password
        self._token = token
        self._enabled = enabled

    def login(self, username: str, password: str) -> str:
        if not self._enabled:
            return self._token
        if verify(username, password, self._username, self._password):
            return self._token
        raise InvalidCredentials()
