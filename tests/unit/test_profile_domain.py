# tests/unit/test_profile_domain.py
import pytest

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


def _profile() -> FinancialProfile:
    return FinancialProfile(
        id="p1",
        income=Income(salary=10_000_000, secondary=3_000_000,
                      avg_bonus_monthly=1_000_000, passive=500_000),
        expenses=[
            Expense("rent", 3_000_000, ExpenseClass.FIXED),
            Expense("food", 3_000_000, ExpenseClass.SEMI_FIXED),
            Expense("transport", 500_000, ExpenseClass.SEMI_FIXED),
            Expense("internet", 300_000, ExpenseClass.FIXED),
            Expense("entertainment", 1_000_000, ExpenseClass.DISCRETIONARY),
        ],
        debts=[
            Debt("credit card", 2_000_000, None, 30.0, None, DebtType.REVOLVING),
            Debt("bnpl laptop", 1_500_000, 9_000_000, 0.0, 6, DebtType.INSTALLMENT),
            Debt("car loan", 2_000_000, 100_000_000, 10.0, 50, DebtType.SECURED),
        ],
        assets=[
            Asset(AssetType.CASH, 20_000_000, Liquidity.HIGH),
            Asset(AssetType.SAVINGS, 80_000_000, Liquidity.MEDIUM),
        ],
        emergency_fund=20_000_000,
        risk=RiskTolerance.MEDIUM,
    )


def test_total_income():
    assert _profile().total_income == 14_500_000


def test_total_expense():
    assert _profile().total_expense == 7_800_000


def test_essential_expense_excludes_discretionary():
    # 3,000,000 + 3,000,000 + 500,000 + 300,000 (no entertainment)
    assert _profile().essential_expense == 6_800_000


def test_total_debt_payment():
    assert _profile().total_debt_payment == 5_500_000


def test_negative_salary_rejected():
    with pytest.raises(ValueError):
        Income(salary=-1)
