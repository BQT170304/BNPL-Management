from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class IncomeIn(BaseModel):
    salary: int = Field(ge=0)
    secondary: int = Field(default=0, ge=0)
    avg_bonus_monthly: int = Field(default=0, ge=0)
    passive: int = Field(default=0, ge=0)


class ExpenseIn(BaseModel):
    category: str
    amount: int = Field(ge=0)
    classification: str


class DebtIn(BaseModel):
    name: str
    monthly_payment: int = Field(ge=0)
    balance: int | None = None
    apr: float = 0.0
    months_remaining: int | None = None
    debt_type: str


class AssetIn(BaseModel):
    type: str
    value: int = Field(ge=0)
    liquidity: str


class GoalIn(BaseModel):
    id: str
    name: str
    target_amount: int = Field(ge=0)
    deadline: date
    priority: str
    savings_allocated: int = Field(default=0, ge=0)


class ProfileIn(BaseModel):
    id: str
    income: IncomeIn
    risk: str
    emergency_fund: int = Field(default=0, ge=0)
    expenses: list[ExpenseIn] = Field(default_factory=list)
    debts: list[DebtIn] = Field(default_factory=list)
    assets: list[AssetIn] = Field(default_factory=list)
    goals: list[GoalIn] = Field(default_factory=list)
