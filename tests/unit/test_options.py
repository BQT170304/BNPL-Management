# tests/unit/test_options.py
from app.modules.advisory.domain.options import (
    PlanSpec,
    PlanType,
    default_plans,
    generate_options,
)


def test_pay_in_full_option():
    opts = generate_options(15_000_000, [PlanSpec(PlanType.PAY_IN_FULL)])
    assert opts[0].type == PlanType.PAY_IN_FULL
    assert opts[0].monthly_payment == 0
    assert opts[0].upfront == 15_000_000


def test_installment_simple_division():
    opts = generate_options(15_000_000, [PlanSpec(PlanType.INSTALLMENT, months=12)])
    assert opts[0].months == 12
    assert opts[0].monthly_payment == 1_250_000
    assert opts[0].upfront == 0


def test_installment_rounds_up():
    opts = generate_options(10_000_000, [PlanSpec(PlanType.INSTALLMENT, months=3)])
    assert opts[0].monthly_payment == 3_333_334  # ceil(10,000,000/3)


def test_installment_with_apr_is_larger():
    plain = generate_options(12_000_000, [PlanSpec(PlanType.INSTALLMENT, months=12)])[0]
    financed = generate_options(
        12_000_000, [PlanSpec(PlanType.INSTALLMENT, months=12, apr=12.0)]
    )[0]
    assert financed.monthly_payment > plain.monthly_payment


def test_default_plans_are_full_3_6_12():
    opts = generate_options(15_000_000, default_plans())
    labels = [(o.type, o.months) for o in opts]
    assert labels == [
        (PlanType.PAY_IN_FULL, None),
        (PlanType.INSTALLMENT, 3),
        (PlanType.INSTALLMENT, 6),
        (PlanType.INSTALLMENT, 12),
    ]
