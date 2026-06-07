from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PortfolioSummary:
    total_customers: int
    evaluated_customers: int
    at_risk_count: int
    early_warned_count: int
    cross_sell_ready_count: int
    total_estimated_obligation: int
    estimated_npl_avoided: int
    assumed_default_reduction_rate: float
