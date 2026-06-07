# app/modules/advisory/application/services.py
from __future__ import annotations

import math
from dataclasses import dataclass

from app.modules.advisory.application.dto import (
    GoalImpact,
    OptionPacket,
    ScoringPacket,
    ScoringResult,
)
from app.modules.advisory.application.ports import RiskScorer
from app.modules.advisory.domain.options import PaymentOption, PlanSpec, PlanType, generate_options
from app.modules.advisory.domain.subscores import SubScores, s_cashflow, s_dti, s_efr, s_goal
from app.modules.analysis.application.services import AnalysisService
from app.modules.analysis.domain.results import GoalMetric, ProfileMetrics
from app.modules.profiles.domain.entities import FinancialProfile
from app.modules.profiles.domain.value_objects import AssetType


@dataclass
class EvaluationResult:
    metrics: ProfileMetrics
    packets: list[OptionPacket]
    scoring: ScoringResult


def _efr_safety(efr_after: float) -> str:
    if efr_after >= 3:
        return "SAFE"
    if efr_after >= 1:
        return "WARNING"
    return "CRITICAL"


def _goal_impacts(
    current_goals: list[GoalMetric],
    new_goals: list[GoalMetric],
) -> list[GoalImpact]:
    impacts = []
    for cur, nw in zip(current_goals, new_goals):
        if math.isinf(cur.gat) or math.isinf(nw.gat):
            # Goal was already unreachable, or becomes unreachable after BNPL.
            # delay=0 here; reachable_by_deadline=False carries the signal.
            delay = 0.0
        else:
            raw = nw.gat - cur.gat
            delay = max(0.0, raw) if not math.isnan(raw) else 0.0

        reachable = (not math.isinf(nw.gat)) and nw.gat <= cur.months_remaining

        if cur.months_remaining > 0 and not math.isinf(nw.gat):
            needed = math.ceil(cur.gap / cur.months_remaining)
            shortfall = max(0, needed - nw.monthly_allocated)
        else:
            shortfall = 0

        impacts.append(GoalImpact(
            goal_id=cur.goal_id,
            name=cur.name,
            delay_months=round(delay, 1),
            reachable_by_deadline=reachable,
            monthly_shortfall=shortfall,
        ))
    return impacts


def _balance_recommendation(packets: list[OptionPacket], purchase_amount: int) -> str:
    """Cross-option balance analysis — answers Q4: most balanced choice.

    Logic (no weights, only thresholds):
    1. Filter out hard-blocked options (NEGATIVE_CASHFLOW / REQUIRES_EMERGENCY_FUND).
    2. Prefer options with EFR SAFE (≥ 3 months).
    3. Among candidates: minimise max per-goal delay, then minimise interest.
    4. Produce a human-readable rationale.
    """
    blocked = {"NEGATIVE_CASHFLOW", "REQUIRES_EMERGENCY_FUND"}

    viable = [p for p in packets if not any(f in blocked for f in p.flags)]
    if not viable:
        return (
            "Tất cả phương án đều vi phạm ràng buộc tài chính. "
            "Khuyến nghị chưa mua hoặc giảm giá trị mua."
        )

    efr_safe = [p for p in viable if p.efr_safety == "SAFE"]
    candidates = efr_safe if efr_safe else viable

    def _sort_key(p: OptionPacket) -> tuple[float, int]:
        max_delay = max((gi.delay_months for gi in p.goal_impacts), default=0.0)
        return (max_delay, p.total_interest)

    best = sorted(candidates, key=_sort_key)[0]
    max_delay = max((gi.delay_months for gi in best.goal_impacts), default=0.0)

    parts: list[str] = [f"Phương án cân bằng nhất: **{best.option.label}**."]

    if best.option.type == PlanType.PAY_IN_FULL:
        parts.append("Không phát sinh lãi, giải phóng dòng tiền ngay từ tháng tiếp theo.")
    else:
        months = best.option.months or 0
        parts.append(
            f"Thanh toán {best.payment:,.0f} ₫/tháng trong {months} tháng"
            + (f", tổng lãi +{best.total_interest:,.0f} ₫." if best.total_interest > 0
               else " (0% lãi suất).")
        )

    if best.efr_safety == "SAFE":
        parts.append(f"Quỹ khẩn cấp còn {best.efr_after:.1f} tháng — an toàn.")
    else:
        parts.append(f"Lưu ý: quỹ khẩn cấp còn {best.efr_after:.1f} tháng (cần bổ sung).")

    if max_delay == 0:
        parts.append("Không làm chậm bất kỳ mục tiêu nào.")
    else:
        delayed = [gi for gi in best.goal_impacts if gi.delay_months > 0]
        delay_strs = [f"'{gi.name}' +{gi.delay_months:.0f} tháng" for gi in delayed[:3]]
        parts.append("Mục tiêu bị ảnh hưởng: " + ", ".join(delay_strs) + ".")

    if not efr_safe and viable:
        parts.append("(Không có phương án nào giữ quỹ khẩn cấp ≥ 3 tháng.)")

    return " ".join(parts)


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

        balance = _balance_recommendation(packets, amount)

        scoring_packet = ScoringPacket(
            profile_id=profile.id, risk_tolerance=profile.risk.value,
            current_ncf=current.ncf, current_dti=current.dti,
            current_efr=current.efr, current_pgrs=current.pgrs,
            item_name=item_name, purchase_amount=amount, options=packets,
        )
        scoring = self._scorer.score(scoring_packet)
        scoring.balance_recommendation = balance

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
            flags.append("REQUIRES_EMERGENCY_FUND")

        sub = SubScores(
            cashflow=s_cashflow(monthly, current.ncf),
            goal=s_goal(with_payment.pgrs - current.pgrs),
            efr=s_efr(with_payment.efr),
            dti=s_dti(with_payment.dti),
        )

        impacts = _goal_impacts(current.goals, with_payment.goals)
        safety = _efr_safety(with_payment.efr)

        months = option.months or 0
        total_cost = monthly * months if months > 0 else amount
        total_interest = max(0, total_cost - amount)

        return OptionPacket(
            option=option, payment=monthly, ncf_new=with_payment.ncf,
            dti_new=with_payment.dti, efr_after=with_payment.efr,
            pgrs_new=with_payment.pgrs, delta_pgrs=with_payment.pgrs - current.pgrs,
            subscores=sub, flags=flags,
            goal_impacts=impacts,
            efr_safety=safety,
            total_interest=total_interest,
        )
