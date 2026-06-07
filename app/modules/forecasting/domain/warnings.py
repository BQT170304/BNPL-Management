from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.modules.forecasting.domain.projection import ForecastResult
from app.modules.profiles.domain.entities import FinancialProfile


class ForecastAlertLevel(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"


@dataclass(frozen=True)
class ForecastAlert:
    """A forward-looking early warning tied to the month it is projected to
    occur, so the user sees risk before creating any plan."""

    code: str
    level: ForecastAlertLevel
    message: str
    recommendation: str
    month: str | None = None


def forecast_alerts(
    forecast: ForecastResult,
    profile: FinancialProfile,
    dti_limit: float = 40.0,
    safe_months: int = 3,
) -> list[ForecastAlert]:
    """Derive proactive alerts from a cashflow projection.

    Each rule reports the *earliest* month it triggers, so the alert carries a
    concrete month, reason, and severity instead of a vague aggregate.
    """

    alerts: list[ForecastAlert] = []
    months = forecast.months
    if not months:
        return alerts

    essential = profile.essential_expense
    safe_buffer = essential * safe_months

    negative = next((m for m in months if m.ending_balance < 0), None)
    if negative is not None:
        alerts.append(ForecastAlert(
            code="PROJECTED_NEGATIVE_BALANCE",
            level=ForecastAlertLevel.CRITICAL,
            message=(
                f"Số dư dự kiến âm vào tháng {negative.month} "
                f"({negative.ending_balance:,} VND)."
            ),
            recommendation="Hoãn khoản mua mới hoặc cắt giảm chi tiêu trước tháng này.",
            month=negative.month,
        ))

    low_buffer = next(
        (m for m in months if 0 <= m.ending_balance < safe_buffer),
        None,
    )
    if low_buffer is not None and negative is None:
        alerts.append(ForecastAlert(
            code="PROJECTED_LOW_BUFFER",
            level=ForecastAlertLevel.WARNING,
            message=(
                f"Số dư dự kiến tháng {low_buffer.month} thấp hơn {safe_months} tháng "
                f"chi thiết yếu ({safe_buffer:,} VND)."
            ),
            recommendation="Giữ quỹ đệm an toàn trước khi nhận nghĩa vụ mới.",
            month=low_buffer.month,
        ))

    dti_pressure = next((m for m in months if m.projected_dti >= dti_limit), None)
    if dti_pressure is not None:
        alerts.append(ForecastAlert(
            code="PROJECTED_DTI_PRESSURE",
            level=ForecastAlertLevel.WARNING,
            message=(
                f"DTI dự kiến tháng {dti_pressure.month} đạt "
                f"{dti_pressure.projected_dti:.1f}% (ngưỡng {dti_limit:.0f}%)."
            ),
            recommendation="Ưu tiên phương án trả hàng tháng thấp hơn hoặc hoãn mua.",
            month=dti_pressure.month,
        ))

    return alerts
