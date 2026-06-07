from __future__ import annotations

import calendar
from datetime import date

from app.core.clock import Clock
from app.modules.forecasting.application.cashflow_forecaster import (
    BaseCashflowForecaster,
    FlatCashflowForecaster,
)
from app.modules.forecasting.application.history_provider import CashflowHistoryProvider
from app.modules.forecasting.domain.projection import (
    ForecastResult,
    ForecastSummary,
    MonthlyProjection,
)
from app.modules.obligations.application.ports import ObligationRepository
from app.modules.obligations.domain.entities import Obligation, ObligationStatus
from app.modules.profiles.domain.entities import FinancialProfile
from app.modules.profiles.domain.value_objects import AssetType


def _add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _month_start(value: date) -> date:
    return date(value.year, value.month, 1)


def _month_end(value: date) -> date:
    return date(value.year, value.month, calendar.monthrange(value.year, value.month)[1])


def _month_key(value: date) -> str:
    return f"{value.year:04d}-{value.month:02d}"


def _month_offset(start: date, month: date) -> int:
    return (month.year - start.year) * 12 + month.month - start.month


def _is_active_in_month(obligation: Obligation, month: date) -> bool:
    if obligation.status != ObligationStatus.ACTIVE:
        return False
    start = _month_start(month)
    end = _month_end(month)
    if obligation.start_date > end:
        return False
    if obligation.end_date is not None and obligation.end_date < start:
        return False
    if obligation.remaining_terms is None:
        return True
    offset = _month_offset(_month_start(obligation.start_date), start)
    return 0 <= offset < obligation.remaining_terms


def _starting_balance(profile: FinancialProfile) -> int:
    liquid_assets = sum(
        asset.value
        for asset in profile.assets
        if asset.type in (AssetType.CASH, AssetType.SAVINGS)
    )
    return liquid_assets if liquid_assets > 0 else profile.emergency_fund


class ForecastService:
    def __init__(
        self,
        clock: Clock,
        obligations: ObligationRepository,
        low_confidence_threshold: float = 0.7,
        base_forecaster: BaseCashflowForecaster | None = None,
        history_provider: CashflowHistoryProvider | None = None,
    ) -> None:
        self._clock = clock
        self._obligations = obligations
        self._low_confidence_threshold = low_confidence_threshold
        self._base_forecaster = base_forecaster or FlatCashflowForecaster()
        self._history_provider = history_provider

    async def forecast(
        self,
        profile: FinancialProfile,
        months: int = 6,
        extra_obligations: list[Obligation] | None = None,
        starting_balance_adjustment: int = 0,
    ) -> ForecastResult:
        if months <= 0:
            raise ValueError("months must be > 0")
        if months > 24:
            raise ValueError("months must be <= 24")

        obligations = await self._obligations.list_by_profile(profile.id)
        if extra_obligations:
            obligations = [*obligations, *extra_obligations]
        current = _month_start(_add_months(self._clock.today(), 1))
        balance = _starting_balance(profile) + starting_balance_adjustment
        projections: list[MonthlyProjection] = []

        current_base = (
            profile.total_income - profile.total_expense - profile.total_debt_payment
        )
        history = (
            await self._history_provider.history_for_profile(profile.id)
            if self._history_provider is not None
            else []
        )
        base_series = self._base_forecaster.forecast_base(history, current_base, months)

        for i in range(months):
            month = _add_months(current, i)
            monthly_obligations = [
                obligation for obligation in obligations
                if _is_active_in_month(obligation, month)
            ]
            obligation_payment = sum(o.monthly_payment for o in monthly_obligations)
            net_cashflow = base_series[i] - obligation_payment
            starting = balance
            ending = starting + net_cashflow
            warnings: list[str] = []
            if net_cashflow < 0:
                warnings.append("NEGATIVE_NET_CASHFLOW")
            if ending < 0:
                warnings.append("NEGATIVE_ENDING_BALANCE")
            if any(
                o.confidence < self._low_confidence_threshold
                for o in monthly_obligations
            ):
                warnings.append("LOW_CONFIDENCE_OBLIGATION")

            projections.append(MonthlyProjection(
                month=_month_key(month),
                income=profile.total_income,
                expense=profile.total_expense,
                debt_payment=profile.total_debt_payment,
                obligation_payment=obligation_payment,
                net_cashflow=net_cashflow,
                starting_balance=starting,
                ending_balance=ending,
                warnings=warnings,
            ))
            balance = ending

        return ForecastResult(
            profile_id=profile.id,
            months=projections,
            summary=ForecastSummary.from_projections(projections),
        )
