import pytest

from app.modules.advisory.domain.subscores import (
    s_cashflow,
    s_dti,
    s_efr,
    s_goal,
)


def test_s_cashflow_bands():
    assert s_cashflow(400_000, 1_000_000) == 100   # 40% -> <=50%
    assert s_cashflow(700_000, 1_000_000) == 60    # 70% -> 50–80%
    assert s_cashflow(900_000, 1_000_000) == 20    # 90% -> 80–100%
    assert s_cashflow(1_100_000, 1_000_000) == 0   # > NCF


def test_s_cashflow_pay_in_full_zero_payment_is_safe():
    assert s_cashflow(0, 1_000_000) == 100


def test_s_cashflow_nonpositive_ncf_is_zero_when_payment_positive():
    assert s_cashflow(100_000, 0) == 0
    assert s_cashflow(0, 0) == 100  # nothing paid monthly


def test_s_goal_continuous():
    assert s_goal(0.0) == 100.0
    assert s_goal(10.0) == 70.0
    assert s_goal(20.0) == 40.0
    assert s_goal(40.0) == 0.0   # min cap


def test_s_efr_bands():
    assert s_efr(6.5) == 100
    assert s_efr(4.0) == 70
    assert s_efr(2.0) == 30
    assert s_efr(0.5) == 0


def test_s_dti_bands():
    assert s_dti(15) == 100
    assert s_dti(30) == 70
    assert s_dti(37) == 40
    assert s_dti(45) == 0
