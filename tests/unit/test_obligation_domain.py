from __future__ import annotations

from datetime import date

import pytest

from app.modules.obligations.domain.entities import Obligation, ObligationType


def _obligation(**overrides: object) -> Obligation:
    values = {
        "id": "obl_1",
        "profile_id": "p1",
        "type": ObligationType.BNPL,
        "merchant": "Store",
        "category": "electronics",
        "principal_amount": 12_000_000,
        "monthly_payment": 2_000_000,
        "due_day": 15,
        "start_date": date(2026, 7, 1),
        "end_date": date(2026, 12, 1),
        "remaining_terms": 6,
    }
    values.update(overrides)
    return Obligation(**values)  # type: ignore[arg-type]


def test_obligation_accepts_valid_values():
    obligation = _obligation()
    assert obligation.id == "obl_1"
    assert obligation.type == ObligationType.BNPL


def test_obligation_rejects_negative_money():
    with pytest.raises(ValueError, match="monthly_payment"):
        _obligation(monthly_payment=-1)


def test_obligation_rejects_invalid_due_day():
    with pytest.raises(ValueError, match="due_day"):
        _obligation(due_day=32)


def test_obligation_rejects_end_date_before_start_date():
    with pytest.raises(ValueError, match="end_date"):
        _obligation(end_date=date(2026, 6, 1))
