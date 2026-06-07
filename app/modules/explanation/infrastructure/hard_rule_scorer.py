"""Final-fallback scorer using only hard binary threshold rules — no weights.

Risk tiers are determined by explicit financial constraints:
  BLOCKED  (100): ncf_new < 0 or requires emergency fund draw
  HIGH     (80):  new DTI > 50%
  ELEVATED (55):  cashflow subscore == 0 (payment > pre-BNPL NCF)
  CAUTION  (38):  new DTI > 40%
  LOW      (18):  all clear

These thresholds mirror industry underwriting cutoffs (DTI 40/50% are
standard hard limits in consumer credit), not arbitrary weights.
"""
from __future__ import annotations

from app.modules.advisory.application.dto import (
    OptionPacket,
    OptionScore,
    ScoringPacket,
    ScoringResult,
)

_BLOCKED_FLAGS = {"NEGATIVE_CASHFLOW", "REQUIRES_EMERGENCY_FUND"}


def _risk_tier(opt: OptionPacket) -> tuple[float, list[str]]:
    if any(f in _BLOCKED_FLAGS for f in opt.flags):
        violated = [f for f in opt.flags if f in _BLOCKED_FLAGS]
        return 100.0, [f"vi phạm ràng buộc: {', '.join(violated)}"]

    if opt.dti_new > 50:
        return 80.0, [f"DTI mới {opt.dti_new:.0f}% > ngưỡng 50%"]

    if opt.subscores.cashflow == 0:
        return 55.0, ["thanh toán vượt dòng tiền ròng hiện tại"]

    if opt.dti_new > 40:
        return 38.0, [f"DTI mới {opt.dti_new:.0f}% ở mức cảnh báo (>40%)"]

    return 18.0, ["các chỉ số tài chính trong ngưỡng an toàn"]


class HardRuleScorer:
    """Risk scoring based entirely on hard threshold rules, no weighted formula."""

    def score(self, packet: ScoringPacket) -> ScoringResult:
        scores: list[OptionScore] = []
        for opt in packet.options:
            risk, factors = _risk_tier(opt)
            blocked = risk == 100.0
            explanation = (
                f"{opt.option.label}: rủi ro {risk:.0f}/100"
                + (" — không khuyến nghị" if blocked else "")
            )
            scores.append(OptionScore(
                option_id=opt.option.id,
                risk_score=risk,
                recommended=not blocked,
                explanation=explanation,
                key_factors=factors,
            ))

        ranked = sorted(scores, key=lambda s: (0 if s.recommended else 1, s.risk_score))
        best = ranked[0].option_id
        return ScoringResult(
            options=scores,
            best_option_id=best,
            summary=f"Phương án ít rủi ro nhất: {best} (risk {ranked[0].risk_score:.0f}/100).",
            scorer_used="hard_rules",
        )
