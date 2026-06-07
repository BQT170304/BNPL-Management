from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, UploadFile, status
from pydantic import BaseModel

from app.dependencies import get_analysis_service, get_repository
from app.modules.analysis.api.schemas import MetricsOut
from app.modules.analysis.application.services import AnalysisService
from app.modules.profiles.api.mappers import from_domain, to_domain
from app.modules.profiles.api.schemas import (
    DebtIn, ExpenseIn, GoalIn, IncomeIn, ProfileIn,
)
from app.modules.profiles.application.ports import ProfileRepository
from app.modules.profiles.application.transaction_extractor import (
    ExtractedProfile, extract_from_bytes,
)

router = APIRouter(tags=["profiles"])


# ── helpers ───────────────────────────────────────────────────────────────────

def _extracted_to_profile_in(ext: ExtractedProfile, profile_id: str | None = None) -> ProfileIn:
    pid = profile_id or f"p-{uuid.uuid4().hex[:12]}"

    expenses: list[ExpenseIn] = []
    if ext.monthly_housing > 0:
        expenses.append(ExpenseIn(category="Nhà ở", amount=ext.monthly_housing, classification="FIXED"))
    if ext.monthly_utilities > 0:
        expenses.append(ExpenseIn(category="Điện / nước / mạng", amount=ext.monthly_utilities, classification="FIXED"))
    if ext.monthly_food > 0:
        expenses.append(ExpenseIn(category="Ăn uống", amount=ext.monthly_food, classification="SEMI_FIXED"))
    if ext.monthly_transport > 0:
        expenses.append(ExpenseIn(category="Đi lại", amount=ext.monthly_transport, classification="SEMI_FIXED"))
    if ext.monthly_health > 0:
        expenses.append(ExpenseIn(category="Y tế / sức khoẻ", amount=ext.monthly_health, classification="SEMI_FIXED"))
    if ext.monthly_education > 0:
        expenses.append(ExpenseIn(category="Học tập", amount=ext.monthly_education, classification="SEMI_FIXED"))
    if ext.monthly_entertainment > 0:
        expenses.append(ExpenseIn(category="Giải trí", amount=ext.monthly_entertainment, classification="DISCRETIONARY"))
    if ext.monthly_shopping > 0:
        expenses.append(ExpenseIn(category="Mua sắm", amount=ext.monthly_shopping, classification="DISCRETIONARY"))
    if ext.monthly_other_expense > 0:
        expenses.append(ExpenseIn(category="Khác", amount=ext.monthly_other_expense, classification="SEMI_FIXED"))

    debts: list[DebtIn] = []
    if ext.monthly_debt_payment > 0:
        debts.append(DebtIn(
            name="Khoản nợ / trả góp",
            monthly_payment=ext.monthly_debt_payment,
            balance=None,
            apr=0.0,
            months_remaining=None,
            debt_type="INSTALLMENT",
        ))

    return ProfileIn(
        id=pid,
        income=IncomeIn(
            salary=ext.salary,
            secondary=ext.secondary,
            avg_bonus_monthly=ext.avg_bonus_monthly,
            passive=ext.passive,
        ),
        risk="MEDIUM",
        emergency_fund=0,
        expenses=expenses,
        debts=debts,
        assets=[],
        goals=[],
    )


class ExtractionSummary(BaseModel):
    months_analyzed: int
    avg_monthly_income: int
    avg_monthly_expense: int
    avg_monthly_net: int
    cif: str


class ExtractResponse(BaseModel):
    suggested_profile: ProfileIn
    summary: ExtractionSummary


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.post("/profiles", status_code=status.HTTP_201_CREATED)
async def create_profile(
    body: ProfileIn, repo: ProfileRepository = Depends(get_repository)
) -> dict[str, str]:
    await repo.add(to_domain(body))
    return {"id": body.id}


@router.get("/profiles/{profile_id}", response_model=ProfileIn)
async def get_profile(
    profile_id: str, repo: ProfileRepository = Depends(get_repository)
) -> ProfileIn:
    profile = await repo.get(profile_id)
    return from_domain(profile)


@router.put("/profiles/{profile_id}", status_code=status.HTTP_200_OK)
async def update_profile(
    profile_id: str,
    body: ProfileIn,
    repo: ProfileRepository = Depends(get_repository),
) -> dict[str, str]:
    await repo.update(to_domain(body))
    return {"id": profile_id}


@router.get("/profiles/{profile_id}/analysis", response_model=MetricsOut)
async def analyze_profile(
    profile_id: str,
    repo: ProfileRepository = Depends(get_repository),
    analysis: AnalysisService = Depends(get_analysis_service),
) -> MetricsOut:
    profile = await repo.get(profile_id)
    return MetricsOut.from_domain(analysis.analyze(profile))


@router.post("/profiles/extract", response_model=ExtractResponse)
async def extract_profile_from_file(
    file: UploadFile = File(...),
) -> ExtractResponse:
    """Upload a transaction CSV/XLSX to extract a suggested financial profile."""
    raw = await file.read()
    filename = file.filename or "upload.csv"
    ext, txns = extract_from_bytes(raw, filename)

    suggested = _extracted_to_profile_in(ext)

    total_income = ext.salary + ext.secondary + ext.avg_bonus_monthly + ext.passive
    total_expense = (
        ext.monthly_housing + ext.monthly_utilities + ext.monthly_food +
        ext.monthly_transport + ext.monthly_health + ext.monthly_education +
        ext.monthly_entertainment + ext.monthly_shopping + ext.monthly_other_expense +
        ext.monthly_debt_payment
    )

    return ExtractResponse(
        suggested_profile=suggested,
        summary=ExtractionSummary(
            months_analyzed=ext.months_analyzed,
            avg_monthly_income=total_income,
            avg_monthly_expense=total_expense,
            avg_monthly_net=total_income - total_expense,
            cif=ext.cif,
        ),
    )
