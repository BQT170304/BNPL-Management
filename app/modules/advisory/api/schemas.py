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


class GoalImpactOut(BaseModel):
    goal_id: str
    goal_name: str
    delay_months: float       # extra months to reach goal vs. baseline
    reachable_by_deadline: bool
    monthly_shortfall: int    # extra VNĐ/month needed to stay on original track


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
    efr_safety: str           # "SAFE" | "WARNING" | "CRITICAL"
    delta_pgrs: float
    total_interest: int       # total VNĐ of interest paid over the term
    flags: list[str]
    goal_impacts: list[GoalImpactOut]   # per-goal delay for this option


class EvaluateOut(BaseModel):
    best_option_id: str
    summary: str
    scorer_used: str
    balance_recommendation: str        # Q4: cross-option balance analysis
    options: list[OptionScoreOut]


# ── Simulation schemas ────────────────────────────────────────────────────────

class SimulateIn(BaseModel):
    profile_id: str
    purchase_amount: int = Field(gt=0)
    option_type: str = "INSTALLMENT"   # "PAY_IN_FULL" | "INSTALLMENT"
    term_months: int | None = None
    apr: float = 0.0
    horizon_months: int = Field(default=24, ge=1, le=60)
    use_forecast: bool = False         # overlay Prophet forecast when True


class CashFlowMonthOut(BaseModel):
    month: int
    year_month: str
    income_forecast: float
    expense_forecast: float
    bnpl_payment: int
    other_debt_payment: int
    net_cashflow: float
    cumulative_balance: float
    goal_savings: float
    warning: str


class ScenarioSimulationOut(BaseModel):
    option_id: str
    label: str
    months: list[CashFlowMonthOut]
    total_bnpl_cost: int
    total_interest: int
    break_even_month: int | None
    goal_impact_summary: str
    risk_level: str


# ── Explain schemas ───────────────────────────────────────────────────────────

class ExplainIn(BaseModel):
    profile_id: str
    item_name: str
    purchase_amount: int = Field(gt=0)
    candidate_plans: list[PlanIn] | None = None


class ExplanationOut(BaseModel):
    payment_recommendation: str
    goal_delay_summary: str
    emergency_fund_assessment: str
    balanced_option_summary: str
    source: str   # "llm" | "template"
