# tests/unit/test_clock.py
from datetime import date

from app.core.clock import FixedClock, SystemClock


def test_fixed_clock_returns_set_date():
    clock = FixedClock(date(2025, 6, 1))
    assert clock.today() == date(2025, 6, 1)


def test_system_clock_returns_a_date():
    assert isinstance(SystemClock().today(), date)
