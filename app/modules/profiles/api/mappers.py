from __future__ import annotations

from app.modules.goals.domain.entities import Goal, Priority
from app.modules.profiles.api.schemas import AssetIn, DebtIn, ExpenseIn, GoalIn, IncomeIn, ProfileIn
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


def from_domain(profile: FinancialProfile) -> ProfileIn:
    return ProfileIn(
        id=profile.id,
        income=IncomeIn(
            salary=profile.income.salary,
            secondary=profile.income.secondary,
            avg_bonus_monthly=profile.income.avg_bonus_monthly,
            passive=profile.income.passive,
        ),
        risk=profile.risk.value,
        emergency_fund=profile.emergency_fund,
        expenses=[
            ExpenseIn(category=e.category, amount=e.amount, classification=e.classification.value)
            for e in profile.expenses
        ],
        debts=[
            DebtIn(
                name=d.name, monthly_payment=d.monthly_payment, balance=d.balance,
                apr=d.apr, months_remaining=d.months_remaining, debt_type=d.debt_type.value,
            )
            for d in profile.debts
        ],
        assets=[
            AssetIn(type=a.type.value, value=a.value, liquidity=a.liquidity.value)
            for a in profile.assets
        ],
        goals=[
            GoalIn(
                id=g.id, name=g.name, target_amount=g.target_amount,
                deadline=g.deadline, priority=g.priority.name,
                savings_allocated=g.savings_allocated,
            )
            for g in profile.goals
        ],
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
