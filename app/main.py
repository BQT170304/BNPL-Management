from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.errors import (
    CifNotFound,
    ConsentNotFound,
    ConsentRequired,
    DecisionNotFound,
    DomainError,
    GoalNotFound,
    ObligationNotFound,
    ProfileNotFound,
)
from app.modules.advisory.api.router import router as advisory_router
from app.modules.consent.api.router import router as consent_router
from app.modules.copilot.api.router import router as copilot_router
from app.modules.decisions.api.router import router as decisions_router
from app.modules.feedback.api.router import router as feedback_router
from app.modules.forecasting.api.router import router as forecasting_router
from app.modules.ingestion.api.router import router as ingestion_router
from app.modules.obligations.api.router import router as obligations_router
from app.modules.planning.api.router import router as planning_router
from app.modules.portfolio.api.router import router as portfolio_router
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
    app.include_router(consent_router)
    app.include_router(ingestion_router)
    app.include_router(obligations_router)
    app.include_router(forecasting_router)
    app.include_router(planning_router)
    app.include_router(decisions_router)
    app.include_router(feedback_router)
    app.include_router(copilot_router)
    app.include_router(portfolio_router)

    @app.exception_handler(ProfileNotFound)
    @app.exception_handler(GoalNotFound)
    @app.exception_handler(CifNotFound)
    @app.exception_handler(ObligationNotFound)
    @app.exception_handler(DecisionNotFound)
    @app.exception_handler(ConsentNotFound)
    async def not_found(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ConsentRequired)
    async def consent_required(_: Request, exc: ConsentRequired) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={
                "detail": str(exc),
                "code": "CONSENT_REQUIRED",
                "cif": exc.cif,
                "scope": exc.scope,
            },
        )

    @app.exception_handler(DomainError)
    async def domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
