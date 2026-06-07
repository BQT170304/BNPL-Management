# app/modules/advisory/application/dto.py
from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.advisory.domain.options import PaymentOption
from app.modules.advisory.domain.subscores import SubScores


@dataclass
class GoalImpact:
    goal_id: str
    name: str
    delay_months: float
    reachable_by_deadline: bool
    monthly_shortfall: int


@dataclass
class OptionPacket:
    option: PaymentOption
    payment: int
    ncf_new: int
    dti_new: float
    efr_after: float
    pgrs_new: float
    delta_pgrs: float
    subscores: SubScores
    flags: list[str] = field(default_factory=list)
    goal_impacts: list[GoalImpact] = field(default_factory=list)
    efr_safety: str = "SAFE"
    total_interest: int = 0


@dataclass
class ScoringPacket:
    profile_id: str
    risk_tolerance: str
    current_ncf: int
    current_dti: float
    current_efr: float
    current_pgrs: float
    item_name: str
    purchase_amount: int
    options: list[OptionPacket]


@dataclass
class OptionScore:
    option_id: str
    risk_score: float        # 0 = safest, 100 = riskiest
    recommended: bool
    explanation: str
    key_factors: list[str] = field(default_factory=list)


@dataclass
class ScoringResult:
    options: list[OptionScore]
    best_option_id: str
    summary: str
    scorer_used: str
    balance_recommendation: str = ""
