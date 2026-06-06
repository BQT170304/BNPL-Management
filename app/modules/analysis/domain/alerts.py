from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.modules.analysis.domain.results import ProfileMetrics


class AlertLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class Alert:
    code: str
    level: AlertLevel
    message: str
    recommendation: str
    affected_value: float | None = None


def check_alerts(metrics: ProfileMetrics) -> list[Alert]:
    """Generate financial health alerts from computed ProfileMetrics."""
    alerts: list[Alert] = []

    # ── Cash flow ────────────────────────────────────────────────────────────
    if metrics.ncf < 0:
        alerts.append(Alert(
            code="NEGATIVE_CASHFLOW",
            level=AlertLevel.CRITICAL,
            message=f"Dòng tiền ròng âm: {metrics.ncf:,.0f} ₫/tháng",
            recommendation="Giảm chi tiêu hoặc tăng thu nhập trước khi mua sắm thêm",
            affected_value=float(metrics.ncf),
        ))
    elif metrics.saving_rate < 10:
        alerts.append(Alert(
            code="LOW_SAVING_RATE",
            level=AlertLevel.WARNING,
            message=f"Tỷ lệ tiết kiệm thấp: {metrics.saving_rate:.1f}%",
            recommendation="Khuyến nghị tiết kiệm ≥ 20% thu nhập",
            affected_value=metrics.saving_rate,
        ))

    # ── Debt-to-income ───────────────────────────────────────────────────────
    if metrics.dti >= 40:
        alerts.append(Alert(
            code="HIGH_DTI",
            level=AlertLevel.CRITICAL,
            message=f"DTI nguy hiểm: {metrics.dti:.1f}%",
            recommendation="Ưu tiên trả nợ trước khi phát sinh khoản vay mới",
            affected_value=metrics.dti,
        ))
    elif metrics.dti >= 35:
        alerts.append(Alert(
            code="WARNING_DTI",
            level=AlertLevel.WARNING,
            message=f"DTI cần chú ý: {metrics.dti:.1f}%",
            recommendation="Hạn chế phát sinh nợ mới",
            affected_value=metrics.dti,
        ))

    # ── Emergency fund ───────────────────────────────────────────────────────
    if metrics.efr < 1:
        alerts.append(Alert(
            code="CRITICAL_EFR",
            level=AlertLevel.CRITICAL,
            message=f"Quỹ khẩn cấp cạn kiệt: {metrics.efr:.1f} tháng",
            recommendation="Xây dựng quỹ khẩn cấp ≥ 3 tháng chi tiêu thiết yếu",
            affected_value=metrics.efr,
        ))
    elif metrics.efr < 3:
        alerts.append(Alert(
            code="LOW_EFR",
            level=AlertLevel.WARNING,
            message=f"Quỹ khẩn cấp chưa đủ: {metrics.efr:.1f} tháng",
            recommendation="Mục tiêu quỹ khẩn cấp là 3–6 tháng chi tiêu thiết yếu",
            affected_value=metrics.efr,
        ))

    # ── Goals ─────────────────────────────────────────────────────────────────
    if metrics.pgrs >= 80:
        alerts.append(Alert(
            code="GOALS_AT_RISK",
            level=AlertLevel.WARNING,
            message=f"Danh mục mục tiêu đang rủi ro cao: PGRS = {metrics.pgrs:.0f}",
            recommendation="Xem xét điều chỉnh mục tiêu hoặc tăng tiết kiệm hàng tháng",
            affected_value=metrics.pgrs,
        ))

    for gm in metrics.goals:
        if gm.grs >= 100 and gm.months_remaining > 0:
            monthly_needed = gm.gap / gm.months_remaining if gm.months_remaining else float("inf")
            alerts.append(Alert(
                code=f"GOAL_UNREACHABLE_{gm.goal_id.upper()[:12]}",
                level=AlertLevel.WARNING,
                message=f"Mục tiêu '{gm.name}' không thể đạt đúng hạn",
                recommendation=f"Cần tiết kiệm thêm ≥ {monthly_needed:,.0f} ₫/tháng",
                affected_value=float(gm.grs),
            ))

    return alerts
