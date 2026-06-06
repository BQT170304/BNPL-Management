# tests/unit/test_goal_domain.py
from datetime import date

import pytest

from app.modules.goals.domain.entities import Goal, Priority


def test_priority_weight():
    assert Priority.VERY_HIGH.weight == 4
    assert Priority.LOW.weight == 1


def test_months_remaining_counts_full_months():
    goal = Goal(id="g1", name="Car", target_amount=300_000_000,
                deadline=date(2027, 12, 1), priority=Priority.HIGH)
    assert goal.months_remaining(date(2025, 6, 1)) == 30


def test_months_remaining_floors_at_zero_when_overdue():
    goal = Goal(id="g1", name="Car", target_amount=1,
                deadline=date(2025, 1, 1), priority=Priority.LOW)
    assert goal.months_remaining(date(2025, 6, 1)) == 0


def test_negative_target_rejected():
    with pytest.raises(ValueError):
        Goal(id="g", name="x", target_amount=-1,
             deadline=date(2030, 1, 1), priority=Priority.LOW)
