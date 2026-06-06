from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class CashFlowMonth:
    month: int            # 0 = current month, 1 = next, …
    year_month: str       # "YYYY-MM"
    income_forecast: float
    expense_forecast: float
    bnpl_payment: int
    other_debt_payment: int
    net_cashflow: float
    cumulative_balance: float
    goal_savings: float
    warning: str = ""     # "", "NEGATIVE_NCF", "LOW_CASHFLOW"


@dataclass
class ScenarioSimulation:
    option_id: str
    label: str
    months: list[CashFlowMonth] = field(default_factory=list)
    total_bnpl_cost: int = 0
    total_interest: int = 0          # above principal
    break_even_month: int | None = None
    goal_impact_summary: str = ""
    risk_level: str = "LOW"          # "LOW" | "MEDIUM" | "HIGH"
