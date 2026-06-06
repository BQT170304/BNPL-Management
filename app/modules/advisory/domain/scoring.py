# app/modules/advisory/domain/scoring.py
from __future__ import annotations

from dataclasses import dataclass

from app.modules.advisory.domain.subscores import SubScores


@dataclass(frozen=True)
class ScoreWeights:
    cashflow: float = 0.35
    goal: float = 0.35
    efr: float = 0.20
    dti: float = 0.10


def weighted_option_score(sub: SubScores, weights: ScoreWeights) -> float:
    """Deterministic weighted option score in [0,100] (higher = better)."""
    return (
        weights.cashflow * sub.cashflow
        + weights.goal * sub.goal
        + weights.efr * sub.efr
        + weights.dti * sub.dti
    )
