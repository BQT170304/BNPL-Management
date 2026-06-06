# app/modules/explanation/infrastructure/deterministic_scorer.py
from __future__ import annotations

from app.modules.advisory.application.dto import (
    OptionPacket,
    OptionScore,
    ScoringPacket,
    ScoringResult,
)
from app.modules.advisory.domain.scoring import ScoreWeights, weighted_option_score

_BLOCKING_FLAGS = {"NEGATIVE_CASHFLOW", "REQUIRES_EMERGENCY_FUND"}


def _factors(packet: OptionPacket) -> list[str]:
    factors: list[str] = []
    if packet.subscores.cashflow >= 60:
        factors.append("dòng tiền an toàn")
    else:
        factors.append("áp lực dòng tiền")
    if packet.delta_pgrs <= 10:
        factors.append("ít ảnh hưởng mục tiêu")
    else:
        factors.append("ảnh hưởng mục tiêu đáng kể")
    if packet.subscores.efr >= 70:
        factors.append("quỹ khẩn cấp ổn")
    if packet.subscores.dti >= 70:
        factors.append("DTI trong ngưỡng an toàn")
    return factors


class DeterministicScorer:
    """Risk = 100 - weighted option score. Higher risk = worse."""

    def __init__(self, weights: ScoreWeights) -> None:
        self._weights = weights

    def score(self, packet: ScoringPacket) -> ScoringResult:
        scores: list[OptionScore] = []
        for opt in packet.options:
            weighted = weighted_option_score(opt.subscores, self._weights)
            risk = round(100.0 - weighted, 1)
            blocked = any(flag in _BLOCKING_FLAGS for flag in opt.flags)
            explanation = (
                f"{opt.option.label}: điểm tổng hợp {weighted:.1f}/100"
                + (" (vi phạm ràng buộc cứng — không khuyến nghị)" if blocked else "")
            )
            scores.append(OptionScore(
                option_id=opt.option.id, risk_score=risk, recommended=not blocked,
                explanation=explanation, key_factors=_factors(opt),
            ))

        # rank: non-blocked first, then ascending risk
        def sort_key(s: OptionScore) -> tuple[int, float]:
            return (0 if s.recommended else 1, s.risk_score)

        ranked = sorted(scores, key=sort_key)
        best = ranked[0].option_id
        summary = f"Phương án rủi ro thấp nhất: {best} (risk {ranked[0].risk_score})."
        return ScoringResult(
            options=scores, best_option_id=best, summary=summary,
            scorer_used="deterministic",
        )
