# app/modules/advisory/domain/options.py
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum


class PlanType(str, Enum):
    PAY_IN_FULL = "PAY_IN_FULL"
    INSTALLMENT = "INSTALLMENT"


@dataclass(frozen=True)
class PlanSpec:
    type: PlanType
    months: int | None = None
    apr: float = 0.0


@dataclass
class PaymentOption:
    id: str
    label: str
    type: PlanType
    months: int | None
    monthly_payment: int
    upfront: int


def default_plans() -> list[PlanSpec]:
    return [
        PlanSpec(PlanType.PAY_IN_FULL),
        PlanSpec(PlanType.INSTALLMENT, months=3),
        PlanSpec(PlanType.INSTALLMENT, months=6),
        PlanSpec(PlanType.INSTALLMENT, months=12),
    ]


def _amortized_monthly(principal: int, months: int, apr: float) -> int:
    if apr <= 0:
        return math.ceil(principal / months)
    r = apr / 100.0 / 12.0
    payment = principal * r / (1 - (1 + r) ** -months)
    return math.ceil(payment)


def generate_options(amount: int, plans: list[PlanSpec]) -> list[PaymentOption]:
    options: list[PaymentOption] = []
    for spec in plans:
        if spec.type == PlanType.PAY_IN_FULL:
            options.append(PaymentOption(
                id="full", label="Trả thẳng 1 lần", type=spec.type,
                months=None, monthly_payment=0, upfront=amount,
            ))
        else:
            months = spec.months or 0
            if months <= 0:
                raise ValueError("installment plan requires months > 0")
            monthly = _amortized_monthly(amount, months, spec.apr)
            options.append(PaymentOption(
                id=f"installment_{months}", label=f"Trả góp {months} tháng",
                type=spec.type, months=months, monthly_payment=monthly, upfront=0,
            ))
    return options
