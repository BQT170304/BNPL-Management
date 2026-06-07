from __future__ import annotations

from fastapi import APIRouter, Depends

import app.dependencies as deps
from app.modules.advisory.api.schemas import (
    CashFlowMonthOut,
    EvaluateIn,
    EvaluateOut,
    ExplainIn,
    ExplanationOut,
    GoalImpactOut,
    OptionScoreOut,
    ScenarioSimulationOut,
    SimulateIn,
)
from app.modules.advisory.application.services import EvaluatePurchaseService
from app.modules.advisory.application.simulator import BNPLSimulator
from app.modules.advisory.domain.options import PlanSpec, PlanType, generate_options, default_plans
from app.modules.analysis.application.services import AnalysisService
from app.modules.explanation.application.explain_service import ExplainService
from app.modules.profiles.application.ports import ProfileRepository

router = APIRouter(tags=["advisory"])


def _evaluate_service() -> EvaluatePurchaseService:
    return deps.get_evaluate_service()


def _repository() -> ProfileRepository:
    return deps.get_repository()


@router.post("/advisory/evaluate", response_model=EvaluateOut)
async def evaluate(
    body: EvaluateIn,
    repo: ProfileRepository = Depends(_repository),
    service: EvaluatePurchaseService = Depends(_evaluate_service),
) -> EvaluateOut:
    profile = await repo.get(body.profile_id)
    plans = (
        [PlanSpec(PlanType(p.type), p.months, p.apr) for p in body.candidate_plans]
        if body.candidate_plans else default_plans()
    )
    result = service.evaluate(profile, body.item_name, body.purchase_amount, plans)
    by_id = {p.option.id: p for p in result.packets}
    options = [
        OptionScoreOut(
            option_id=s.option_id, risk_score=s.risk_score, recommended=s.recommended,
            explanation=s.explanation, key_factors=s.key_factors,
            monthly_payment=by_id[s.option_id].payment,
            ncf_new=by_id[s.option_id].ncf_new,
            dti_new=by_id[s.option_id].dti_new,
            efr_after=by_id[s.option_id].efr_after,
            efr_safety=by_id[s.option_id].efr_safety,
            delta_pgrs=by_id[s.option_id].delta_pgrs,
            total_interest=by_id[s.option_id].total_interest,
            flags=by_id[s.option_id].flags,
            goal_impacts=[
                GoalImpactOut(
                    goal_id=gi.goal_id, goal_name=gi.name,
                    delay_months=gi.delay_months,
                    reachable_by_deadline=gi.reachable_by_deadline,
                    monthly_shortfall=gi.monthly_shortfall,
                )
                for gi in by_id[s.option_id].goal_impacts
            ],
        )
        for s in result.scoring.options
    ]
    return EvaluateOut(
        best_option_id=result.scoring.best_option_id,
        summary=result.scoring.summary,
        scorer_used=result.scoring.scorer_used,
        balance_recommendation=result.scoring.balance_recommendation,
        options=options,
    )


@router.post("/advisory/simulate", response_model=ScenarioSimulationOut)
async def simulate(
    body: SimulateIn,
    repo: ProfileRepository = Depends(_repository),
    analysis_svc: AnalysisService = Depends(deps.get_analysis_service),
) -> ScenarioSimulationOut:
    """Month-by-month cash flow simulation for a single BNPL option."""
    profile = await repo.get(body.profile_id)
    metrics = analysis_svc.analyze(profile)

    spec = PlanSpec(PlanType(body.option_type), body.term_months, body.apr)
    option = generate_options(body.purchase_amount, [spec])[0]

    monthly_forecast = None
    if body.use_forecast:
        try:
            forecast_svc = deps.get_forecast_service()
            cif = body.cif or getattr(profile, "cif", None) or profile.id
            result = forecast_svc.forecast(cif)
            monthly_forecast = _aggregate_monthly(result.forecast)
        except Exception:
            pass  # fall back to flat profile figures

    sim = BNPLSimulator().simulate(
        profile, metrics, option,
        horizon_months=body.horizon_months,
        monthly_forecast=monthly_forecast,
    )
    return ScenarioSimulationOut(
        option_id=sim.option_id, label=sim.label,
        months=[CashFlowMonthOut(**m.__dict__) for m in sim.months],
        total_bnpl_cost=sim.total_bnpl_cost, total_interest=sim.total_interest,
        break_even_month=sim.break_even_month,
        goal_impact_summary=sim.goal_impact_summary, risk_level=sim.risk_level,
    )


@router.post("/advisory/explain", response_model=ExplanationOut)
async def explain(
    body: ExplainIn,
    repo: ProfileRepository = Depends(_repository),
    service: EvaluatePurchaseService = Depends(_evaluate_service),
    explain_svc: ExplainService = Depends(deps.get_explain_service),
) -> ExplanationOut:
    """Answer the 4 user questions in plain Vietnamese (no raw metrics)."""
    profile = await repo.get(body.profile_id)
    plans = (
        [PlanSpec(PlanType(p.type), p.months, p.apr) for p in body.candidate_plans]
        if body.candidate_plans else default_plans()
    )
    result = service.evaluate(profile, body.item_name, body.purchase_amount, plans)
    explanation = explain_svc.explain(result)
    return ExplanationOut(
        payment_recommendation=explanation.payment_recommendation,
        goal_delay_summary=explanation.goal_delay_summary,
        emergency_fund_assessment=explanation.emergency_fund_assessment,
        balanced_option_summary=explanation.balanced_option_summary,
        source=explanation.source,
    )


def _aggregate_monthly(
    forecast: list,  # list[ForecastPoint]
) -> list[tuple[str, float]]:
    """Sum daily Prophet forecasts into (YYYY-MM, net_cashflow) pairs."""
    monthly: dict[str, float] = {}
    for pt in forecast:
        ym = pt.ds.strftime("%Y-%m")
        monthly[ym] = monthly.get(ym, 0.0) + pt.yhat
    return sorted(monthly.items())
