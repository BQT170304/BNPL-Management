# app/modules/analysis/domain/allocation.py
from __future__ import annotations

from typing import Protocol

from app.core.money import share_split
from app.modules.goals.domain.entities import Goal


class AllocationStrategy(Protocol):
    def allocate(self, ncf: int, goals: list[Goal]) -> dict[str, int]:
        """Map goal.id -> monthly amount allocated from NCF. Negative NCF -> all 0."""
        ...


class EvenAllocation:
    def allocate(self, ncf: int, goals: list[Goal]) -> dict[str, int]:
        if not goals:
            return {}
        budget = max(0, ncf)
        shares = share_split(budget, [1 for _ in goals])
        return {g.id: s for g, s in zip(goals, shares, strict=True)}


class PriorityWeightedAllocation:
    def allocate(self, ncf: int, goals: list[Goal]) -> dict[str, int]:
        if not goals:
            return {}
        budget = max(0, ncf)
        shares = share_split(budget, [g.priority.weight for g in goals])
        return {g.id: s for g, s in zip(goals, shares, strict=True)}


def get_strategy(name: str) -> AllocationStrategy:
    return EvenAllocation() if name.lower() == "even" else PriorityWeightedAllocation()
