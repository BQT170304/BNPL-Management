from __future__ import annotations

from pydantic import BaseModel, Field


class PlanIn(BaseModel):
    type: str                      # "PAY_IN_FULL" | "INSTALLMENT"
    months: int | None = None
    apr: float = 0.0


class EvaluateIn(BaseModel):
    profile_id: str
    item_name: str
    purchase_amount: int = Field(gt=0)
    candidate_plans: list[PlanIn] | None = None


class OptionScoreOut(BaseModel):
    option_id: str
    risk_score: float
    recommended: bool
    explanation: str
    key_factors: list[str]
    monthly_payment: int
    ncf_new: int
    dti_new: float
    efr_after: float
    delta_pgrs: float
    flags: list[str]


class EvaluateOut(BaseModel):
    best_option_id: str
    summary: str
    scorer_used: str
    options: list[OptionScoreOut]
