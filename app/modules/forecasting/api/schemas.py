from __future__ import annotations

from pydantic import BaseModel

from app.modules.forecasting.domain.daily import DailyForecastPoint, DailyForecastResult
from app.modules.forecasting.domain.projection import (
    ForecastResult,
    ForecastSummary,
    MonthlyProjection,
)


class MonthlyProjectionOut(BaseModel):
    month: str
    income: int
    expense: int
    debt_payment: int
    obligation_payment: int
    net_cashflow: int
    starting_balance: int
    ending_balance: int
    warnings: list[str]

    @classmethod
    def from_domain(cls, projection: MonthlyProjection) -> MonthlyProjectionOut:
        return cls(
            month=projection.month,
            income=projection.income,
            expense=projection.expense,
            debt_payment=projection.debt_payment,
            obligation_payment=projection.obligation_payment,
            net_cashflow=projection.net_cashflow,
            starting_balance=projection.starting_balance,
            ending_balance=projection.ending_balance,
            warnings=projection.warnings,
        )


class ForecastSummaryOut(BaseModel):
    next_30_net: int
    next_90_net: int
    min_projected_balance: int

    @classmethod
    def from_domain(cls, summary: ForecastSummary) -> ForecastSummaryOut:
        return cls(
            next_30_net=summary.next_30_net,
            next_90_net=summary.next_90_net,
            min_projected_balance=summary.min_projected_balance,
        )


class ForecastOut(BaseModel):
    profile_id: str
    months: list[MonthlyProjectionOut]
    summary: ForecastSummaryOut

    @classmethod
    def from_domain(cls, forecast: ForecastResult) -> ForecastOut:
        return cls(
            profile_id=forecast.profile_id,
            months=[MonthlyProjectionOut.from_domain(month) for month in forecast.months],
            summary=ForecastSummaryOut.from_domain(forecast.summary),
        )


class DailyForecastPointOut(BaseModel):
    date: str
    predicted_net: int
    lower: int
    upper: int
    projected_balance: int

    @classmethod
    def from_domain(cls, p: DailyForecastPoint) -> DailyForecastPointOut:
        return cls(date=p.date, predicted_net=p.predicted_net, lower=p.lower,
                   upper=p.upper, projected_balance=p.projected_balance)


class DailyForecastOut(BaseModel):
    profile_id: str
    engine: str
    history_days: int
    days: int
    starting_balance: int
    min_projected_balance: int
    points: list[DailyForecastPointOut]

    @classmethod
    def from_domain(cls, r: DailyForecastResult) -> DailyForecastOut:
        return cls(profile_id=r.profile_id, engine=r.engine, history_days=r.history_days,
                   days=r.days, starting_balance=r.starting_balance,
                   min_projected_balance=r.min_projected_balance,
                   points=[DailyForecastPointOut.from_domain(p) for p in r.points])
