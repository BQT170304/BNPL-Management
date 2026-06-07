from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import (
    get_constraint_optimizer,
    get_decision_service,
    get_repository,
    get_scenario_simulator,
)
from app.modules.decisions.application.services import DecisionService
from app.modules.planning.api.schemas import RecommendOut, SimulateIn, SimulateOut
from app.modules.planning.application.optimizer import ConstraintOptimizer
from app.modules.planning.application.simulator import ScenarioSimulator
from app.modules.profiles.application.ports import ProfileRepository

router = APIRouter(tags=["planning"])


@router.post("/planning/simulate", response_model=SimulateOut)
async def simulate(
    body: SimulateIn,
    repo: ProfileRepository = Depends(get_repository),
    simulator: ScenarioSimulator = Depends(get_scenario_simulator),
) -> SimulateOut:
    profile = await repo.get(body.profile_id)
    result = await simulator.simulate(
        profile,
        item_name=body.item_name,
        amount=body.amount,
        horizon_months=body.horizon_months,
        terms=body.to_terms(),
        tenor=body.tenor,
    )
    return SimulateOut.from_domain(result)


@router.post("/planning/recommend", response_model=RecommendOut)
async def recommend(
    body: SimulateIn,
    repo: ProfileRepository = Depends(get_repository),
    optimizer: ConstraintOptimizer = Depends(get_constraint_optimizer),
    decisions: DecisionService = Depends(get_decision_service),
) -> RecommendOut:
    profile = await repo.get(body.profile_id)
    result = await optimizer.recommend(
        profile,
        item_name=body.item_name,
        amount=body.amount,
        horizon_months=body.horizon_months,
        terms=body.to_terms(),
        tenor=body.tenor,
    )
    decision_id = None
    if body.record:
        trace = await decisions.record(result, input_snapshot=body.model_dump())
        decision_id = trace.id
    return RecommendOut.from_domain(result, decision_id=decision_id)
