from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_portfolio_service
from app.modules.portfolio.api.schemas import PortfolioSummaryOut
from app.modules.portfolio.application.services import PortfolioService

router = APIRouter(tags=["portfolio"])


@router.get("/portfolio/summary", response_model=PortfolioSummaryOut)
async def portfolio_summary(
    limit: int | None = Query(default=None, ge=1, le=5000),
    service: PortfolioService = Depends(get_portfolio_service),
) -> PortfolioSummaryOut:
    return PortfolioSummaryOut.from_domain(service.summarize(limit=limit))
