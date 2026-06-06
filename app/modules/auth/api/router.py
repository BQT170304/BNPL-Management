from __future__ import annotations

from fastapi import APIRouter, Depends

import app.dependencies as deps
from app.modules.auth.api.schemas import LoginIn, TokenOut
from app.modules.auth.application.service import AuthService

router = APIRouter(tags=["auth"])


def _service() -> AuthService:
    # Indirection so tests can monkeypatch deps.get_auth_service.
    return deps.get_auth_service()


@router.post("/auth/login", response_model=TokenOut)
async def login(body: LoginIn, service: AuthService = Depends(_service)) -> TokenOut:
    return TokenOut(token=service.login(body.username, body.password))
