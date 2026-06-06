from __future__ import annotations

from app.modules.goals.domain.entities import Goal, Priority
from app.modules.profiles.api.schemas import ProfileIn
from app.modules.profiles.domain.entities import (
    Asset,
    Debt,
    Expense,
    FinancialProfile,
    Income,
)
from app.modules.profiles.domain.value_objects import (
    AssetType,
    DebtType,
    ExpenseClass,
    Liquidity,
    RiskTolerance,
)


def to_domain(body: ProfileIn) -> FinancialProfile:
    return FinancialProfile(
        id=body.id,
        income=Income(**body.income.model_dump()),
        risk=RiskTolerance(body.risk),
        emergency_fund=body.emergency_fund,
        expenses=[Expense(e.category, e.amount, ExpenseClass(e.classification))
                  for e in body.expenses],
        debts=[Debt(d.name, d.monthly_payment, d.balance, d.apr,
                    d.months_remaining, DebtType(d.debt_type)) for d in body.debts],
        assets=[Asset(AssetType(a.type), a.value, Liquidity(a.liquidity))
                for a in body.assets],
        goals=[Goal(g.id, g.name, g.target_amount, g.deadline,
                    Priority[g.priority], g.savings_allocated) for g in body.goals],
    )
