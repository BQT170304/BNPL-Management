from datetime import date

from app.core.clock import FixedClock
from app.modules.advisory.application.services import EvaluatePurchaseService
from app.modules.advisory.domain.options import default_plans
from app.modules.analysis.application.services import AnalysisService
from app.modules.analysis.domain.allocation import EvenAllocation
from app.modules.explanation.infrastructure.hard_rule_scorer import HardRuleScorer
from app.modules.goals.domain.entities import Goal, Priority
from app.modules.profiles.domain.entities import Debt, Expense, FinancialProfile, Income
from app.modules.profiles.domain.value_objects import DebtType, ExpenseClass, RiskTolerance


def _profile() -> FinancialProfile:
    return FinancialProfile(
        id="p1",
        income=Income(10_000_000, 3_000_000, 1_000_000, 500_000),
        risk=RiskTolerance.MEDIUM, emergency_fund=20_000_000,
        expenses=[
            Expense("rent", 3_000_000, ExpenseClass.FIXED),
            Expense("food", 3_000_000, ExpenseClass.SEMI_FIXED),
            Expense("transport", 500_000, ExpenseClass.SEMI_FIXED),
            Expense("internet", 300_000, ExpenseClass.FIXED),
            Expense("fun", 1_000_000, ExpenseClass.DISCRETIONARY),
        ],
        debts=[Debt("cc", 2_000_000, None, 30.0, None, DebtType.REVOLVING),
               Debt("bnpl", 1_500_000, 9_000_000, 0.0, 6, DebtType.INSTALLMENT),
               Debt("car", 2_000_000, 100_000_000, 10.0, 50, DebtType.SECURED)],
        goals=[Goal("car", "Car", 300_000_000, date(2027, 12, 1), Priority.HIGH),
               Goal("house", "House", 1_000_000_000, date(2034, 12, 1), Priority.VERY_HIGH),
               Goal("japan", "Japan", 50_000_000, date(2026, 12, 1), Priority.MEDIUM)],
    )


def _service() -> EvaluatePurchaseService:
    analysis = AnalysisService(FixedClock(date(2025, 6, 1)), EvenAllocation())
    return EvaluatePurchaseService(analysis=analysis, scorer=HardRuleScorer())


def test_evaluate_returns_one_score_per_option():
    result = _service().evaluate(_profile(), "Phone", 15_000_000, default_plans())
    assert {o.option_id for o in result.scoring.options} == {
        "full", "installment_3", "installment_6", "installment_12",
    }
    assert result.metrics.ncf == 1_200_000


def test_evaluate_flags_negative_cashflow_options():
    result = _service().evaluate(_profile(), "Phone", 15_000_000, default_plans())
    inst3 = next(p for p in result.packets if p.option.id == "installment_3")
    assert "NEGATIVE_CASHFLOW" in inst3.flags


def test_evaluate_pay_in_full_requires_emergency_fund_flag_when_cash_short():
    result = _service().evaluate(_profile(), "Car", 150_000_000, default_plans())
    full = next(p for p in result.packets if p.option.id == "full")
    assert "REQUIRES_EMERGENCY_FUND" in full.flags


def test_hard_rule_scorer_used():
    result = _service().evaluate(_profile(), "Phone", 15_000_000, default_plans())
    assert result.scoring.scorer_used == "hard_rules"
