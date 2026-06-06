# tests/unit/test_analysis_service.py
from datetime import date

import pytest

from app.core.clock import FixedClock
from app.modules.analysis.application.services import AnalysisService
from app.modules.analysis.domain.allocation import EvenAllocation
from app.modules.analysis.domain.thresholds import DtiBand
from app.modules.goals.domain.entities import Goal, Priority
from app.modules.profiles.domain.entities import (
    Debt,
    Expense,
    FinancialProfile,
    Income,
)
from app.modules.profiles.domain.value_objects import (
    DebtType,
    ExpenseClass,
    RiskTolerance,
)


def _profile() -> FinancialProfile:
    return FinancialProfile(
        id="p1",
        income=Income(10_000_000, 3_000_000, 1_000_000, 500_000),
        risk=RiskTolerance.MEDIUM,
        emergency_fund=20_000_000,
        expenses=[
            Expense("rent", 3_000_000, ExpenseClass.FIXED),
            Expense("food", 3_000_000, ExpenseClass.SEMI_FIXED),
            Expense("transport", 500_000, ExpenseClass.SEMI_FIXED),
            Expense("internet", 300_000, ExpenseClass.FIXED),
            Expense("fun", 1_000_000, ExpenseClass.DISCRETIONARY),
        ],
        debts=[
            Debt("cc", 2_000_000, None, 30.0, None, DebtType.REVOLVING),
            Debt("bnpl", 1_500_000, 9_000_000, 0.0, 6, DebtType.INSTALLMENT),
            Debt("car", 2_000_000, 100_000_000, 10.0, 50, DebtType.SECURED),
        ],
        goals=[
            Goal("car", "Car", 300_000_000, date(2027, 12, 1), Priority.HIGH),
            Goal("house", "House", 1_000_000_000, date(2034, 12, 1), Priority.VERY_HIGH),
            Goal("japan", "Japan", 50_000_000, date(2026, 12, 1), Priority.MEDIUM),
        ],
    )


def test_analyze_matches_spec_golden_numbers():
    svc = AnalysisService(clock=FixedClock(date(2025, 6, 1)), allocation=EvenAllocation())
    m = svc.analyze(_profile())

    assert m.ncf == 1_200_000
    assert m.dti == pytest.approx(37.93, abs=0.01)
    assert m.dti_band == DtiBand.WARNING
    assert m.efr == pytest.approx(2.94, abs=0.01)        # 20,000,000 / 6,800,000
    assert m.saving_rate == pytest.approx(8.28, abs=0.01)
    # NCF too low to reach any goal on time -> all GRS 100 -> PGRS 100
    assert m.pgrs == pytest.approx(100.0)
    assert {g.goal_id for g in m.goals} == {"car", "house", "japan"}


def test_analyze_with_extra_payment_lowers_ncf_and_saving_rate():
    svc = AnalysisService(clock=FixedClock(date(2025, 6, 1)), allocation=EvenAllocation())
    m = svc.analyze(_profile(), new_payment=2_000_000)
    # NCF for allocation reflects the new payment: 1,200,000 - 2,000,000 = -800,000
    assert m.ncf == -800_000
    assert m.saving_rate == pytest.approx((-800_000) / 14_500_000 * 100, abs=0.01)
