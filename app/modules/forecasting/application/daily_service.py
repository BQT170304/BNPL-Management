from __future__ import annotations

from app.modules.forecasting.application.daily_forecaster import forecast_daily
from app.modules.forecasting.application.daily_history import DailyHistoryProvider
from app.modules.forecasting.domain.daily import DailyForecastResult
from app.modules.profiles.domain.entities import FinancialProfile
from app.modules.profiles.domain.value_objects import AssetType


def _liquid_balance(profile: FinancialProfile) -> int:
    liquid = sum(
        a.value for a in profile.assets if a.type in (AssetType.CASH, AssetType.SAVINGS)
    )
    return liquid if liquid > 0 else profile.emergency_fund


class DailyForecastService:
    def __init__(self, history_provider: DailyHistoryProvider) -> None:
        self._history = history_provider

    async def forecast(self, profile: FinancialProfile, days: int = 90) -> DailyForecastResult:
        history = await self._history.daily_net_for_profile(profile.id)
        return forecast_daily(profile.id, history, days, _liquid_balance(profile))
