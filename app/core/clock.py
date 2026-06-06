# app/core/clock.py
from __future__ import annotations

from datetime import date
from typing import Protocol


class Clock(Protocol):
    def today(self) -> date: ...


class SystemClock:
    def today(self) -> date:
        return date.today()


class FixedClock:
    def __init__(self, value: date) -> None:
        self._value = value

    def today(self) -> date:
        return self._value
