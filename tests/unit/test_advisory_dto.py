# tests/unit/test_advisory_dto.py
from app.modules.advisory.application.dto import (
    OptionPacket,
    OptionScore,
    ScoringResult,
)
from app.modules.advisory.domain.options import PaymentOption, PlanType
from app.modules.advisory.domain.subscores import SubScores


def test_option_packet_holds_metrics_and_flags():
    opt = PaymentOption("full", "Trả thẳng", PlanType.PAY_IN_FULL, None, 0, 15_000_000)
    packet = OptionPacket(
        option=opt, payment=0, ncf_new=1_200_000, dti_new=37.9, efr_after=2.94,
        pgrs_new=100.0, delta_pgrs=0.0,
        subscores=SubScores(100, 100.0, 30, 40), flags=["REQUIRES_EMERGENCY_FUND"],
    )
    assert packet.flags == ["REQUIRES_EMERGENCY_FUND"]
    assert packet.option.id == "full"


def test_scoring_result_round_trips():
    result = ScoringResult(
        options=[OptionScore("full", 52.0, True, "ok", ["cashflow"])],
        best_option_id="full", summary="done", scorer_used="deterministic",
    )
    assert result.best_option_id == "full"
    assert result.options[0].risk_score == 52.0
