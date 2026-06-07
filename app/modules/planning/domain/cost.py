from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class FinancingTerms:
    """Provider/product financing terms for a purchase."""

    apr: float = 0.0
    fee: int = 0
    late_fee: int = 0
    merchant_subsidy: int = 0

    def __post_init__(self) -> None:
        if self.apr < 0:
            raise ValueError("apr must be >= 0")
        if self.fee < 0:
            raise ValueError("fee must be >= 0")
        if self.late_fee < 0:
            raise ValueError("late_fee must be >= 0")
        if self.merchant_subsidy < 0:
            raise ValueError("merchant_subsidy must be >= 0")


@dataclass(frozen=True)
class CostBreakdown:
    monthly_payment: int
    total_interest: int
    total_fee: int
    late_fee: int
    merchant_subsidy: int
    total_cost: int
    break_even_month: int | None


def amortized_monthly_payment(principal: int, apr: float, months: int) -> int:
    """Fixed monthly payment for an amortising loan, rounded up to whole VND."""

    if months <= 0 or principal <= 0:
        return 0
    monthly_rate = apr / 12.0 / 100.0
    if monthly_rate <= 0:
        return math.ceil(principal / months)
    factor = (1 + monthly_rate) ** months
    payment = principal * monthly_rate * factor / (factor - 1)
    return math.ceil(payment)


def compute_cost(
    *,
    amount: int,
    upfront: int,
    principal: int,
    months: int | None,
    terms: FinancingTerms,
) -> CostBreakdown:
    """Compute the true cost of a financing scenario.

    ``total_cost`` is everything the buyer pays for the item across the
    scenario, net of any merchant subsidy. ``break_even_month`` is when
    cumulative outlay first covers the cash sticker price.
    """

    if months and principal > 0:
        monthly = amortized_monthly_payment(principal, terms.apr, months)
        total_payments = monthly * months
        total_interest = max(0, total_payments - principal)
    else:
        monthly = 0
        total_payments = 0
        total_interest = 0

    total_cost = upfront + total_payments + terms.fee - terms.merchant_subsidy

    if monthly > 0:
        financed = max(0, amount - upfront)
        break_even = min(months or 1, max(1, math.ceil(financed / monthly)))
    else:
        break_even = 1

    return CostBreakdown(
        monthly_payment=monthly,
        total_interest=total_interest,
        total_fee=terms.fee,
        late_fee=terms.late_fee,
        merchant_subsidy=terms.merchant_subsidy,
        total_cost=total_cost,
        break_even_month=break_even,
    )
