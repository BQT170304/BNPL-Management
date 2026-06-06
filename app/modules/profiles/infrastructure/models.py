from __future__ import annotations

from datetime import date

from sqlalchemy import BigInteger, Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProfileModel(Base):
    __tablename__ = "financial_profiles"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    salary: Mapped[int] = mapped_column(BigInteger)
    secondary: Mapped[int] = mapped_column(BigInteger, default=0)
    avg_bonus_monthly: Mapped[int] = mapped_column(BigInteger, default=0)
    passive: Mapped[int] = mapped_column(BigInteger, default=0)
    emergency_fund: Mapped[int] = mapped_column(BigInteger, default=0)
    risk: Mapped[str] = mapped_column(String)

    expenses: Mapped[list[ExpenseModel]] = relationship(
        cascade="all, delete-orphan", lazy="selectin")
    debts: Mapped[list[DebtModel]] = relationship(
        cascade="all, delete-orphan", lazy="selectin")
    assets: Mapped[list[AssetModel]] = relationship(
        cascade="all, delete-orphan", lazy="selectin")
    goals: Mapped[list[GoalModel]] = relationship(
        cascade="all, delete-orphan", lazy="selectin")


class ExpenseModel(Base):
    __tablename__ = "expenses"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_id: Mapped[str] = mapped_column(ForeignKey("financial_profiles.id"), index=True)
    category: Mapped[str] = mapped_column(String)
    amount: Mapped[int] = mapped_column(BigInteger)
    classification: Mapped[str] = mapped_column(String)


class DebtModel(Base):
    __tablename__ = "debts"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_id: Mapped[str] = mapped_column(ForeignKey("financial_profiles.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    monthly_payment: Mapped[int] = mapped_column(BigInteger)
    balance: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    apr: Mapped[float] = mapped_column(Float, default=0.0)
    months_remaining: Mapped[int | None] = mapped_column(nullable=True)
    debt_type: Mapped[str] = mapped_column(String)


class AssetModel(Base):
    __tablename__ = "assets"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_id: Mapped[str] = mapped_column(ForeignKey("financial_profiles.id"), index=True)
    type: Mapped[str] = mapped_column(String)
    value: Mapped[int] = mapped_column(BigInteger)
    liquidity: Mapped[str] = mapped_column(String)


class GoalModel(Base):
    __tablename__ = "goals"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    profile_id: Mapped[str] = mapped_column(ForeignKey("financial_profiles.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    target_amount: Mapped[int] = mapped_column(BigInteger)
    deadline: Mapped[date] = mapped_column(Date)
    priority: Mapped[str] = mapped_column(String)
    savings_allocated: Mapped[int] = mapped_column(BigInteger, default=0)
