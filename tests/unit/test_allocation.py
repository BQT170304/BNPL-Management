# tests/unit/test_allocation.py
from datetime import date

from app.modules.analysis.domain.allocation import EvenAllocation, PriorityWeightedAllocation
from app.modules.goals.domain.entities import Goal, Priority


def _goals():
    return [
        Goal("car", "Car", 300_000_000, date(2027, 12, 1), Priority.HIGH),
        Goal("house", "House", 1_000_000_000, date(2034, 12, 1), Priority.VERY_HIGH),
        Goal("japan", "Japan", 50_000_000, date(2026, 12, 1), Priority.MEDIUM),
    ]


def test_even_allocation_splits_equally():
    alloc = EvenAllocation().allocate(1_200_000, _goals())
    assert alloc == {"car": 400_000, "house": 400_000, "japan": 400_000}


def test_even_allocation_negative_ncf_is_zero():
    alloc = EvenAllocation().allocate(-800_000, _goals())
    assert alloc == {"car": 0, "house": 0, "japan": 0}


def test_weighted_allocation_by_priority_weight():
    # weights 3,4,2 over 900_000 -> 300k,400k,200k
    alloc = PriorityWeightedAllocation().allocate(900_000, _goals())
    assert alloc == {"car": 300_000, "house": 400_000, "japan": 200_000}


def test_allocation_no_goals_returns_empty():
    assert EvenAllocation().allocate(1_000_000, []) == {}
