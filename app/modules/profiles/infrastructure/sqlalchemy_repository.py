from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.errors import ProfileNotFound
from app.modules.goals.domain.entities import Goal, Priority
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
from app.modules.profiles.infrastructure.models import (
    AssetModel,
    DebtModel,
    ExpenseModel,
    GoalModel,
    ProfileModel,
)


def _to_model(p: FinancialProfile) -> ProfileModel:
    return ProfileModel(
        id=p.id, salary=p.income.salary, secondary=p.income.secondary,
        avg_bonus_monthly=p.income.avg_bonus_monthly, passive=p.income.passive,
        emergency_fund=p.emergency_fund, risk=p.risk.value,
        expenses=[ExpenseModel(category=e.category, amount=e.amount,
                               classification=e.classification.value) for e in p.expenses],
        debts=[DebtModel(name=d.name, monthly_payment=d.monthly_payment, balance=d.balance,
                         apr=d.apr, months_remaining=d.months_remaining,
                         debt_type=d.debt_type.value) for d in p.debts],
        assets=[AssetModel(type=a.type.value, value=a.value, liquidity=a.liquidity.value)
                for a in p.assets],
        goals=[GoalModel(id=g.id, name=g.name, target_amount=g.target_amount,
                         deadline=g.deadline, priority=g.priority.name,
                         savings_allocated=g.savings_allocated) for g in p.goals],
    )


def _to_domain(m: ProfileModel) -> FinancialProfile:
    return FinancialProfile(
        id=m.id,
        income=Income(m.salary, m.secondary, m.avg_bonus_monthly, m.passive),
        risk=RiskTolerance(m.risk), emergency_fund=m.emergency_fund,
        expenses=[Expense(e.category, e.amount, ExpenseClass(e.classification))
                  for e in m.expenses],
        debts=[Debt(d.name, d.monthly_payment, d.balance, d.apr,
                    d.months_remaining, DebtType(d.debt_type)) for d in m.debts],
        assets=[Asset(AssetType(a.type), a.value, Liquidity(a.liquidity)) for a in m.assets],
        goals=[Goal(g.id, g.name, g.target_amount, g.deadline,
                    Priority[g.priority], g.savings_allocated) for g in m.goals],
    )


class SqlAlchemyProfileRepository:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker

    async def add(self, profile: FinancialProfile) -> None:
        async with self._sessionmaker() as session:
            existing = await session.get(ProfileModel, profile.id)
            if existing is not None:
                await session.delete(existing)
                await session.flush()
            session.add(_to_model(profile))
            await session.commit()

    async def get(self, profile_id: str) -> FinancialProfile:
        async with self._sessionmaker() as session:
            model = await session.get(ProfileModel, profile_id)
            if model is None:
                raise ProfileNotFound(profile_id)
            return _to_domain(model)

    async def update(self, profile: FinancialProfile) -> None:
        async with self._sessionmaker() as session:
            existing = await session.get(ProfileModel, profile.id)
            if existing is None:
                raise ProfileNotFound(profile.id)
            await session.delete(existing)
            await session.flush()
            session.add(_to_model(profile))
            await session.commit()
