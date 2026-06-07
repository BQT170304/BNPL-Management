from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.modules.analysis.domain.results import ProfileMetrics


class AlertLevel(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"


@dataclass(frozen=True)
class FinancialAlert:
    code: str
    level: AlertLevel
    message: str
    recommendation: str


def check_alerts(metrics: ProfileMetrics) -> list[FinancialAlert]:
    alerts: list[FinancialAlert] = []
    if metrics.ncf < 0:
        alerts.append(FinancialAlert(
            code="NEGATIVE_NCF",
            level=AlertLevel.CRITICAL,
            message="Dòng tiền ròng đang âm.",
            recommendation="Tạm dừng BNPL mới và giảm chi tiêu tùy chọn trước.",
        ))
    if metrics.dti >= 40:
        alerts.append(FinancialAlert(
            code="DTI_DANGER",
            level=AlertLevel.CRITICAL,
            message="DTI vượt ngưỡng 40%.",
            recommendation="Không nên phát sinh nghĩa vụ trả góp mới.",
        ))
    elif metrics.dti >= 35:
        alerts.append(FinancialAlert(
            code="DTI_WARNING",
            level=AlertLevel.WARNING,
            message="DTI đang ở vùng cảnh báo.",
            recommendation="Ưu tiên plan có trả hàng tháng thấp hoặc hoãn mua.",
        ))
    if metrics.efr < 1:
        alerts.append(FinancialAlert(
            code="EFR_CRITICAL",
            level=AlertLevel.CRITICAL,
            message="Quỹ khẩn cấp dưới 1 tháng chi thiết yếu.",
            recommendation="Tăng quỹ khẩn cấp trước khi nhận nghĩa vụ mới.",
        ))
    elif metrics.efr < 3:
        alerts.append(FinancialAlert(
            code="EFR_WARNING",
            level=AlertLevel.WARNING,
            message="Quỹ khẩn cấp dưới mức khuyến nghị 3 tháng.",
            recommendation="Giữ BNPL ở kỳ hạn nhẹ dòng tiền hoặc hoãn mua.",
        ))
    if metrics.saving_rate < 10:
        alerts.append(FinancialAlert(
            code="LOW_SAVING_RATE",
            level=AlertLevel.WARNING,
            message="Tỷ lệ tiết kiệm dưới 10%.",
            recommendation="Đặt ngân sách chi tiêu trước khi mua thêm.",
        ))
    delayed_goals = [g for g in metrics.goals if g.delay > 0]
    if delayed_goals:
        alerts.append(FinancialAlert(
            code="GOAL_DELAY",
            level=AlertLevel.WARNING,
            message="Một hoặc nhiều mục tiêu tài chính đang bị trễ.",
            recommendation="Chọn phương án làm tăng nghĩa vụ hàng tháng ít nhất.",
        ))
    return alerts
