# app/modules/analysis/domain/formulas.py
"""Pure financial formulas. No I/O, no clock, no DB. All amounts are int VNĐ."""
from __future__ import annotations

from app.core.money import percent, ratio


def net_cash_flow(income: int, expense: int, debt_payment: int) -> int:
    """NCF = income - expense - debt payment."""
    return income - expense - debt_payment


def dti(debt_payment: int, income: int) -> float:
    """Debt-to-income ratio as a percentage."""
    return percent(debt_payment, income)


def saving_rate(ncf: int, new_purchase_payment: int, income: int) -> float:
    """(NCF - new purchase payment) / income, as a percentage."""
    return percent(ncf - new_purchase_payment, income)


def efr(emergency_fund: int, essential_expense: int) -> float:
    """Emergency-fund ratio in months of essential expense."""
    return ratio(emergency_fund, essential_expense)


def goal_gap(target: int, savings_allocated: int) -> int:
    """Remaining amount to reach a goal."""
    return max(0, target - savings_allocated)


def gat(gap: int, monthly_saving_allocated: int) -> float:
    """Goal achievement time in months. Zero/negative allocation -> inf."""
    if monthly_saving_allocated <= 0:
        return float("inf") if gap > 0 else 0.0
    return gap / monthly_saving_allocated


def goal_delay(gat_value: float, months_remaining: int) -> float:
    """Months late vs. the deadline. Positive = late."""
    return gat_value - months_remaining


def grs(delay: float, months_remaining: int) -> float:
    """Goal risk score 0..100. Overdue (months_remaining<=0) -> 100."""
    if months_remaining <= 0:
        return 100.0
    return min(100.0, max(0.0, delay / months_remaining * 100.0))


def pgrs(grs_weighted: list[tuple[float, int]]) -> float:
    """Portfolio goal risk: weighted average of per-goal GRS. No goals -> 0."""
    weight_sum = sum(w for _, w in grs_weighted)
    if weight_sum == 0:
        return 0.0
    return sum(score * w for score, w in grs_weighted) / weight_sum
