# app/modules/profiles/domain/entities.py
from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.goals.domain.entities import Goal
from app.modules.profiles.domain.value_objects import (
    AssetType,
    DebtType,
    ExpenseClass,
    Liquidity,
    RiskTolerance,
)


@dataclass
class Income:
    salary: int
    secondary: int = 0
    avg_bonus_monthly: int = 0
    passive: int = 0

    def __post_init__(self) -> None:
        for name in ("salary", "secondary", "avg_bonus_monthly", "passive"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be >= 0")

    @property
    def total(self) -> int:
        return self.salary + self.secondary + self.avg_bonus_monthly + self.passive


@dataclass
class Expense:
    category: str
    amount: int
    classification: ExpenseClass

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("expense amount must be >= 0")


@dataclass
class Debt:
    name: str
    monthly_payment: int
    balance: int | None
    apr: float
    months_remaining: int | None
    debt_type: DebtType

    def __post_init__(self) -> None:
        if self.monthly_payment < 0:
            raise ValueError("monthly_payment must be >= 0")


@dataclass
class Asset:
    type: AssetType
    value: int
    liquidity: Liquidity

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("asset value must be >= 0")


@dataclass
class FinancialProfile:
    id: str
    income: Income
    risk: RiskTolerance
    emergency_fund: int = 0
    expenses: list[Expense] = field(default_factory=list)
    debts: list[Debt] = field(default_factory=list)
    assets: list[Asset] = field(default_factory=list)
    goals: list[Goal] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.emergency_fund < 0:
            raise ValueError("emergency_fund must be >= 0")

    @property
    def total_income(self) -> int:
        return self.income.total

    @property
    def total_expense(self) -> int:
        return sum(e.amount for e in self.expenses)

    @property
    def essential_expense(self) -> int:
        return sum(
            e.amount for e in self.expenses
            if e.classification in (ExpenseClass.FIXED, ExpenseClass.SEMI_FIXED)
        )

    @property
    def total_debt_payment(self) -> int:
        return sum(d.monthly_payment for d in self.debts)
