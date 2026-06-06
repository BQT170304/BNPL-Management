# app/modules/advisory/application/services.py
from __future__ import annotations

from dataclasses import dataclass

from app.modules.advisory.application.dto import OptionPacket, ScoringPacket, ScoringResult
from app.modules.advisory.application.ports import RiskScorer
from app.modules.advisory.domain.options import PaymentOption, PlanSpec, PlanType, generate_options
from app.modules.advisory.domain.subscores import SubScores, s_cashflow, s_dti, s_efr, s_goal
from app.modules.analysis.application.services import AnalysisService
from app.modules.analysis.domain.results import ProfileMetrics
from app.modules.profiles.domain.entities import FinancialProfile
from app.modules.profiles.domain.value_objects import AssetType


@dataclass
class EvaluationResult:
    metrics: ProfileMetrics
    packets: list[OptionPacket]
    scoring: ScoringResult


class EvaluatePurchaseService:
    def __init__(self, analysis: AnalysisService, scorer: RiskScorer) -> None:
        self._analysis = analysis
        self._scorer = scorer

    def evaluate(
        self, profile: FinancialProfile, item_name: str, amount: int,
        plans: list[PlanSpec],
    ) -> EvaluationResult:
        current = self._analysis.analyze(profile)
        liquid_cash = sum(
            a.value for a in profile.assets
            if a.type in (AssetType.CASH, AssetType.SAVINGS)
        )

        packets = [
            self._build_packet(profile, current, option, amount, liquid_cash)
            for option in generate_options(amount, plans)
        ]
        packet = ScoringPacket(
            profile_id=profile.id, risk_tolerance=profile.risk.value,
            current_ncf=current.ncf, current_dti=current.dti,
            current_efr=current.efr, current_pgrs=current.pgrs,
            item_name=item_name, purchase_amount=amount, options=packets,
        )
        scoring = self._scorer.score(packet)
        return EvaluationResult(metrics=current, packets=packets, scoring=scoring)

    def _build_packet(
        self, profile: FinancialProfile, current: ProfileMetrics,
        option: PaymentOption, amount: int, liquid_cash: int,
    ) -> OptionPacket:
        monthly = option.monthly_payment
        with_payment = self._analysis.analyze(profile, new_payment=monthly)
        flags: list[str] = []
        if with_payment.ncf < 0:
            flags.append("NEGATIVE_CASHFLOW")

        if option.type == PlanType.PAY_IN_FULL and option.upfront > liquid_cash:
            # paying in full would force drawing the emergency fund
            flags.append("REQUIRES_EMERGENCY_FUND")

        sub = SubScores(
            cashflow=s_cashflow(monthly, current.ncf),
            goal=s_goal(with_payment.pgrs - current.pgrs),
            efr=s_efr(with_payment.efr),
            dti=s_dti(with_payment.dti),
        )
        return OptionPacket(
            option=option, payment=monthly, ncf_new=with_payment.ncf,
            dti_new=with_payment.dti, efr_after=with_payment.efr,
            pgrs_new=with_payment.pgrs, delta_pgrs=with_payment.pgrs - current.pgrs,
            subscores=sub, flags=flags,
        )
