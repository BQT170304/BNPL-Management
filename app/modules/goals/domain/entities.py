# app/modules/goals/domain/entities.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import IntEnum


class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    VERY_HIGH = 4

    @property
    def weight(self) -> int:
        return int(self.value)


@dataclass
class Goal:
    id: str
    name: str
    target_amount: int
    deadline: date
    priority: Priority
    savings_allocated: int = 0

    def __post_init__(self) -> None:
        if self.target_amount < 0:
            raise ValueError("target_amount must be >= 0")
        if self.savings_allocated < 0:
            raise ValueError("savings_allocated must be >= 0")

    def months_remaining(self, today: date) -> int:
        months = (self.deadline.year - today.year) * 12 + (self.deadline.month - today.month)
        return max(0, months)
