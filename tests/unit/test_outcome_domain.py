from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.modules.feedback.domain.entities import Outcome, RepaymentOutcome

NOW = datetime(2026, 6, 6, tzinfo=UTC)


def test_outcome_classification():
    assert RepaymentOutcome.PAID_ON_TIME.is_good
    assert not RepaymentOutcome.PAID_ON_TIME.is_bad
    assert RepaymentOutcome.DEFAULT.is_bad
    assert RepaymentOutcome.MISSED.is_bad
    assert not RepaymentOutcome.LATE.is_good
    assert not RepaymentOutcome.LATE.is_bad
    assert not RepaymentOutcome.RESTRUCTURED.is_bad


def _outcome(**kwargs) -> Outcome:
    base = dict(
        id="out_1",
        decision_id="dec_1",
        profile_id="p1",
        outcome=RepaymentOutcome.PAID_ON_TIME,
        recorded_by="rm",
        recorded_at=NOW,
    )
    base.update(kwargs)
    return Outcome(**base)


def test_outcome_requires_decision_and_recorder():
    with pytest.raises(ValueError):
        _outcome(decision_id="")
    with pytest.raises(ValueError):
        _outcome(recorded_by="")
