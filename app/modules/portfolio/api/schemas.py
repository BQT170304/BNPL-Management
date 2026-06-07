from __future__ import annotations

from pydantic import BaseModel

from app.modules.portfolio.domain.results import PortfolioSummary


class PortfolioSummaryOut(BaseModel):
    total_customers: int
    evaluated_customers: int
    at_risk_count: int
    early_warned_count: int
    cross_sell_ready_count: int
    total_estimated_obligation: int
    estimated_npl_avoided: int
    assumed_default_reduction_rate: float

    @classmethod
    def from_domain(cls, summary: PortfolioSummary) -> PortfolioSummaryOut:
        return cls(**summary.__dict__)
