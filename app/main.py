from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.errors import CifNotFound, DomainError, GoalNotFound, ProfileNotFound
from app.modules.advisory.api.router import router as advisory_router
from app.modules.ingestion.api.router import router as ingestion_router
from app.modules.profiles.api.router import router as profiles_router


def create_app() -> FastAPI:
    app = FastAPI(title="BNPL Assistant", version="0.1.0")

    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(profiles_router)
    app.include_router(advisory_router)
    app.include_router(ingestion_router)

    @app.exception_handler(ProfileNotFound)
    @app.exception_handler(GoalNotFound)
    @app.exception_handler(CifNotFound)
    async def not_found(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(DomainError)
    async def domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
