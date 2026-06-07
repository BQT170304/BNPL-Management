from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MonthlyProjection:
    month: str
    income: int
    expense: int
    debt_payment: int
    obligation_payment: int
    net_cashflow: int
    starting_balance: int
    ending_balance: int
    warnings: list[str] = field(default_factory=list)

    @property
    def projected_dti(self) -> float:
        if self.income <= 0:
            return 0.0
        return (self.debt_payment + self.obligation_payment) / self.income * 100.0


@dataclass(frozen=True)
class ForecastSummary:
    """Headline forward-looking numbers for proactive early warning."""

    next_30_net: int
    next_90_net: int
    min_projected_balance: int

    @classmethod
    def from_projections(cls, months: list[MonthlyProjection]) -> ForecastSummary:
        if not months:
            return cls(next_30_net=0, next_90_net=0, min_projected_balance=0)
        next_30_net = months[0].net_cashflow
        next_90_net = sum(month.net_cashflow for month in months[:3])
        min_projected_balance = min(month.ending_balance for month in months)
        return cls(
            next_30_net=next_30_net,
            next_90_net=next_90_net,
            min_projected_balance=min_projected_balance,
        )


@dataclass(frozen=True)
class ForecastResult:
    profile_id: str
    months: list[MonthlyProjection]
    summary: ForecastSummary
