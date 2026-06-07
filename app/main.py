from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, FastAPI, Request
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
    InvalidCredentials,
    ObligationNotFound,
    ProfileNotFound,
    Unauthorized,
)
from app.modules.advisory.api.router import router as advisory_router
from app.modules.analysis.api.router import router as analysis_router
from app.modules.auth.api.router import router as auth_router
from app.modules.auth.api.security import require_auth
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

DEMO_PROFILE_ID = "demo-profile"


async def _seed_demo_profile() -> None:
    from app.dependencies import get_repository
    from app.modules.goals.domain.entities import Goal, Priority
    from app.modules.profiles.domain.entities import (
        Asset, Debt, Expense, FinancialProfile, Income,
    )
    from app.modules.profiles.domain.value_objects import (
        AssetType, DebtType, ExpenseClass, Liquidity, RiskTolerance,
    )

    from sqlalchemy.exc import IntegrityError

    repo = get_repository()
    try:
        await repo.get(DEMO_PROFILE_ID)
        return  # already seeded
    except ProfileNotFound:
        pass

    # Profile trích xuất từ 18 tháng giao dịch CIF 10001234 (lập trình viên 27 tuổi)
    demo = FinancialProfile(
        id=DEMO_PROFILE_ID,
        income=Income(
            salary=19_000_000,
            secondary=2_500_000,   # thu nhập freelance
            avg_bonus_monthly=600_000,  # thưởng quý / 3
            passive=0,
        ),
        risk=RiskTolerance.MEDIUM,
        emergency_fund=15_000_000,
        expenses=[
            Expense("Nhà ở", 4_500_000, ExpenseClass.FIXED),
            Expense("Điện / nước / mạng", 850_000, ExpenseClass.FIXED),
            Expense("Ăn uống", 3_500_000, ExpenseClass.SEMI_FIXED),
            Expense("Đi lại", 1_200_000, ExpenseClass.SEMI_FIXED),
            Expense("Y tế / sức khoẻ", 250_000, ExpenseClass.SEMI_FIXED),
            Expense("Giải trí", 800_000, ExpenseClass.DISCRETIONARY),
            Expense("Mua sắm", 900_000, ExpenseClass.DISCRETIONARY),
        ],
        debts=[
            Debt(
                name="Trả góp điện thoại",
                monthly_payment=2_200_000,
                balance=8_800_000,
                apr=0.0,
                months_remaining=4,
                debt_type=DebtType.INSTALLMENT,
            ),
            Debt(
                name="Thẻ tín dụng",
                monthly_payment=1_000_000,
                balance=None,
                apr=18.0,
                months_remaining=None,
                debt_type=DebtType.REVOLVING,
            ),
        ],
        assets=[
            Asset(AssetType.SAVINGS, 15_000_000, Liquidity.HIGH),
        ],
        goals=[
            Goal(
                id="g-demo-ef",
                name="Quỹ khẩn cấp 6 tháng",
                target_amount=130_000_000,
                deadline=date(2027, 6, 1),
                priority=Priority.VERY_HIGH,
                savings_allocated=2_000_000,
            ),
            Goal(
                id="g-demo-car",
                name="Mua ô tô",
                target_amount=600_000_000,
                deadline=date(2029, 1, 1),
                priority=Priority.HIGH,
                savings_allocated=2_000_000,
            ),
            Goal(
                id="g-demo-trip",
                name="Du lịch Nhật Bản",
                target_amount=50_000_000,
                deadline=date(2026, 12, 1),
                priority=Priority.MEDIUM,
                savings_allocated=1_500_000,
            ),
        ],
    )
    try:
        await repo.add(demo)
    except IntegrityError:
        pass  # another worker already inserted it (race on startup)


def create_app() -> FastAPI:
    app = FastAPI(title="BNPL Assistant", version="0.1.0")

    @app.on_event("startup")
    async def _init_db() -> None:
        from app.dependencies import get_db_engine
        from app.core.database import Base
        import app.modules.profiles.infrastructure.models  # noqa: F401 — registers ORM tables
        engine = get_db_engine()
        if engine is not None:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        await _seed_demo_profile()

    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    protected = [Depends(require_auth)]
    api = APIRouter(prefix="/api")
    api.include_router(auth_router)
    api.include_router(profiles_router, dependencies=protected)
    api.include_router(advisory_router, dependencies=protected)
    api.include_router(analysis_router, dependencies=protected)
    api.include_router(consent_router, dependencies=protected)
    api.include_router(ingestion_router, dependencies=protected)
    api.include_router(obligations_router, dependencies=protected)
    api.include_router(forecasting_router, dependencies=protected)
    api.include_router(planning_router, dependencies=protected)
    api.include_router(decisions_router, dependencies=protected)
    api.include_router(feedback_router, dependencies=protected)
    api.include_router(copilot_router, dependencies=protected)
    api.include_router(portfolio_router, dependencies=protected)
    app.include_router(api)

    @app.exception_handler(ProfileNotFound)
    @app.exception_handler(GoalNotFound)
    @app.exception_handler(CifNotFound)
    @app.exception_handler(ObligationNotFound)
    @app.exception_handler(DecisionNotFound)
    @app.exception_handler(ConsentNotFound)
    async def not_found(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(InvalidCredentials)
    @app.exception_handler(Unauthorized)
    async def unauthorized(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=401, content={"detail": str(exc)})

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
    @api.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @api.get("/demo-profile-id")
    async def demo_profile_id() -> dict[str, str]:
        return {"id": DEMO_PROFILE_ID}

    return app


app = create_app()
