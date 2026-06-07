from __future__ import annotations

from app.core.money import percent
from app.modules.ingestion.application.service import IngestionService
from app.modules.portfolio.domain.results import PortfolioSummary


class PortfolioService:
    def __init__(
        self,
        ingestion: IngestionService,
        assumed_default_reduction_rate: float = 0.15,
    ) -> None:
        self._ingestion = ingestion
        self._assumed_default_reduction_rate = assumed_default_reduction_rate

    def summarize(self, limit: int | None = None) -> PortfolioSummary:
        cifs = self._ingestion.list_cifs()
        selected = cifs[:limit] if limit else cifs
        at_risk = 0
        cross_sell_ready = 0
        total_obligation = 0

        for cif in selected:
            seed = self._ingestion.get_seed(cif)
            obligations = self._ingestion.get_obligation_seeds(cif, limit=5)
            monthly_obligation = sum(o.monthly_payment for o in obligations)
            total_obligation += sum(o.total_paid for o in obligations)
            projected_ncf = seed.income - seed.expense - seed.debt_payment - monthly_obligation
            dti = percent(seed.debt_payment + monthly_obligation, seed.income)
            if projected_ncf < 0 or dti >= 40:
                at_risk += 1
            elif projected_ncf > 0 and dti < 35:
                cross_sell_ready += 1

        return PortfolioSummary(
            total_customers=len(cifs),
            evaluated_customers=len(selected),
            at_risk_count=at_risk,
            early_warned_count=at_risk,
            cross_sell_ready_count=cross_sell_ready,
            total_estimated_obligation=total_obligation,
            estimated_npl_avoided=int(
                total_obligation * self._assumed_default_reduction_rate
            ),
            assumed_default_reduction_rate=self._assumed_default_reduction_rate,
        )
