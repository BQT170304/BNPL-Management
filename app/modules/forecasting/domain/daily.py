from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DailyForecastPoint:
    date: str  # YYYY-MM-DD
    predicted_net: int
    lower: int
    upper: int
    projected_balance: int


@dataclass(frozen=True)
class DailyForecastResult:
    profile_id: str
    engine: str          # "prophet" | "fallback"
    history_days: int
    days: int
    starting_balance: int
    min_projected_balance: int
    points: list[DailyForecastPoint] = field(default_factory=list)
