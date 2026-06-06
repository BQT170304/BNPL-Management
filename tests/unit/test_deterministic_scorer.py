# tests/unit/test_deterministic_scorer.py
from app.modules.advisory.application.dto import OptionPacket, ScoringPacket
from app.modules.advisory.domain.options import PaymentOption, PlanType
from app.modules.advisory.domain.scoring import ScoreWeights
from app.modules.advisory.domain.subscores import SubScores
from app.modules.explanation.infrastructure.deterministic_scorer import DeterministicScorer


def _packet() -> ScoringPacket:
    full = PaymentOption("full", "Trả thẳng", PlanType.PAY_IN_FULL, None, 0, 15_000_000)
    inst = PaymentOption("installment_12", "Trả góp 12", PlanType.INSTALLMENT, 12, 1_250_000, 0)
    return ScoringPacket(
        profile_id="p1", risk_tolerance="MEDIUM",
        current_ncf=1_200_000, current_dti=37.9, current_efr=2.94, current_pgrs=100.0,
        item_name="Phone", purchase_amount=15_000_000,
        options=[
            OptionPacket(full, 0, -13_800_000, 37.9, 2.94, 100.0, 0.0,
                         SubScores(100, 100.0, 30, 40), flags=["NEGATIVE_CASHFLOW"]),
            OptionPacket(inst, 1_250_000, -50_000, 46.5, 2.94, 100.0, 8.0,
                         SubScores(20, 76.0, 30, 0), flags=["NEGATIVE_CASHFLOW"]),
        ],
    )


def test_risk_is_100_minus_weighted_score():
    scorer = DeterministicScorer(ScoreWeights())
    result = scorer.score(_packet())
    # full: .35*100+.35*100+.20*30+.10*40 = 35+35+6+4 = 80 -> risk 20
    full = next(o for o in result.options if o.option_id == "full")
    assert full.risk_score == 20.0
    assert result.scorer_used == "deterministic"


def test_best_option_is_lowest_risk():
    result = DeterministicScorer(ScoreWeights()).score(_packet())
    # full risk 20 vs installment_12: .35*20+.35*76+.20*30+.10*0=7+26.6+6+0=39.6 -> risk 60.4
    assert result.best_option_id == "full"


def test_negative_cashflow_option_marked_not_recommended():
    result = DeterministicScorer(ScoreWeights()).score(_packet())
    assert all(o.recommended is False for o in result.options)
