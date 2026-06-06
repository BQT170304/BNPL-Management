# app/modules/advisory/application/ports.py
from __future__ import annotations

from typing import Protocol

from app.modules.advisory.application.dto import ScoringPacket, ScoringResult


class RiskScorer(Protocol):
    def score(self, packet: ScoringPacket) -> ScoringResult:
        """Assign a 0–100 risk score per option and choose the best."""
        ...
