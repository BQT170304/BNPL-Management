from __future__ import annotations

import pytest

from app.modules.planning.domain.cost import (
    FinancingTerms,
    amortized_monthly_payment,
    compute_cost,
)


def test_zero_principal_payment_is_zero():
    assert amortized_monthly_payment(0, 12.0, 6) == 0
    assert amortized_monthly_payment(1_000_000, 12.0, 0) == 0


def test_zero_apr_is_simple_division():
    assert amortized_monthly_payment(12_000_000, 0.0, 6) == 2_000_000


def test_positive_apr_adds_interest():
    monthly = amortized_monthly_payment(12_000_000, 24.0, 6)
    assert monthly > 2_000_000


def test_pay_full_cost():
    cost = compute_cost(
        amount=10_000_000,
        upfront=10_000_000,
        principal=0,
        months=None,
        terms=FinancingTerms(fee=200_000),
    )
    assert cost.monthly_payment == 0
    assert cost.total_interest == 0
    assert cost.total_cost == 10_200_000
    assert cost.break_even_month == 1


def test_bnpl_zero_apr_cost():
    cost = compute_cost(
        amount=12_000_000,
        upfront=0,
        principal=12_000_000,
        months=6,
        terms=FinancingTerms(),
    )
    assert cost.monthly_payment == 2_000_000
    assert cost.total_interest == 0
    assert cost.total_cost == 12_000_000
    assert cost.break_even_month == 6


def test_bnpl_with_apr_has_interest_and_total_cost():
    cost = compute_cost(
        amount=12_000_000,
        upfront=0,
        principal=12_000_000,
        months=12,
        terms=FinancingTerms(apr=36.0, fee=300_000),
    )
    assert cost.total_interest > 0
    assert cost.total_cost > 12_000_000 + 300_000 - 1  # interest on top of principal+fee


def test_merchant_subsidy_reduces_total_cost():
    base = compute_cost(amount=10_000_000, upfront=0, principal=10_000_000,
                        months=6, terms=FinancingTerms(apr=24.0))
    subsidised = compute_cost(amount=10_000_000, upfront=0, principal=10_000_000,
                              months=6, terms=FinancingTerms(apr=24.0, merchant_subsidy=500_000))
    assert subsidised.total_cost == base.total_cost - 500_000


def test_financing_terms_reject_negative():
    with pytest.raises(ValueError):
        FinancingTerms(apr=-1)
    with pytest.raises(ValueError):
        FinancingTerms(fee=-1)
