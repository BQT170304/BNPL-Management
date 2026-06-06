from __future__ import annotations

from fastapi import Header

from app.core.config import get_settings
from app.core.errors import Unauthorized


async def require_auth(authorization: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if not settings.auth_enabled:
        return
    expected = f"Bearer {settings.auth_token}"
    if authorization != expected:
        raise Unauthorized("Missing or invalid authentication token")
