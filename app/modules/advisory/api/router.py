from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_evaluate_service, get_repository
from app.modules.advisory.api.schemas import EvaluateIn, EvaluateOut, OptionScoreOut
from app.modules.advisory.application.services import EvaluatePurchaseService
from app.modules.advisory.domain.options import PlanSpec, PlanType, default_plans
from app.modules.profiles.application.ports import ProfileRepository

router = APIRouter(tags=["advisory"])


@router.post("/advisory/evaluate", response_model=EvaluateOut)
async def evaluate(
    body: EvaluateIn,
    repo: ProfileRepository = Depends(get_repository),
    service: EvaluatePurchaseService = Depends(get_evaluate_service),
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
            ncf_new=by_id[s.option_id].ncf_new, dti_new=by_id[s.option_id].dti_new,
            efr_after=by_id[s.option_id].efr_after,
            delta_pgrs=by_id[s.option_id].delta_pgrs, flags=by_id[s.option_id].flags,
        )
        for s in result.scoring.options
    ]
    return EvaluateOut(
        best_option_id=result.scoring.best_option_id, summary=result.scoring.summary,
        scorer_used=result.scoring.scorer_used, options=options,
    )
