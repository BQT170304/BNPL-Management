from __future__ import annotations

from app.modules.analysis.domain.alerts import check_alerts
from app.modules.analysis.domain.results import ProfileMetrics
from app.modules.analysis.domain.thresholds import DtiBand


def test_check_alerts_for_critical_financial_health():
    alerts = check_alerts(ProfileMetrics(
        ncf=-1,
        dti=42,
        dti_band=DtiBand.DANGER,
        saving_rate=0,
        efr=0.5,
        pgrs=0,
    ))

    codes = {alert.code for alert in alerts}
    assert {"NEGATIVE_NCF", "DTI_DANGER", "EFR_CRITICAL", "LOW_SAVING_RATE"} <= codes


def test_check_alerts_for_warning_financial_health():
    alerts = check_alerts(ProfileMetrics(
        ncf=1_000_000,
        dti=36,
        dti_band=DtiBand.WARNING,
        saving_rate=8,
        efr=2,
        pgrs=0,
    ))

    codes = {alert.code for alert in alerts}
    assert {"DTI_WARNING", "EFR_WARNING", "LOW_SAVING_RATE"} <= codes
