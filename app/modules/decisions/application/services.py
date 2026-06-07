from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.modules.decisions.application.ports import DecisionRepository
from app.modules.decisions.domain.entities import (
    DecisionExplanation,
    DecisionOverride,
    DecisionTrace,
    OverrideAction,
)
from app.modules.planning.domain.constraints import RecommendationResult, ScenarioDecision


class DecisionService:
    def __init__(
        self,
        repository: DecisionRepository,
        model_version: str = "deterministic-v1",
    ) -> None:
        self._repository = repository
        self._model_version = model_version

    async def record(
        self,
        recommendation: RecommendationResult,
        input_snapshot: dict[str, Any],
    ) -> DecisionTrace:
        trace = DecisionTrace(
            id=f"dec_{uuid4().hex}",
            profile_id=recommendation.profile_id,
            input_snapshot=input_snapshot,
            recommendation=recommendation,
            model_version=self._model_version,
            created_at=datetime.now(UTC),
        )
        await self._repository.add(trace)
        return trace

    async def get(self, decision_id: str) -> DecisionTrace:
        return await self._repository.get(decision_id)

    async def override(
        self,
        decision_id: str,
        actor: str,
        action: str,
        reason: str,
        scenario_id: str | None = None,
    ) -> DecisionTrace:
        """Record a human decision next to the machine decision (never replaces
        it), with a mandatory reason and actor for the audit trail."""

        trace = await self._repository.get(decision_id)
        override = DecisionOverride(
            decision_id=decision_id,
            actor=actor,
            action=OverrideAction(action),
            reason=reason,
            created_at=datetime.now(UTC),
            scenario_id=scenario_id,
        )
        updated = replace(trace, override=override)
        await self._repository.update(updated)
        return updated

    async def explain(self, decision_id: str) -> DecisionExplanation:
        trace = await self.get(decision_id)
        recommendation = trace.recommendation
        selected = next((d for d in recommendation.scenarios if d.recommended), None)
        if selected is None:
            return DecisionExplanation(
                decision_id=decision_id,
                summary=recommendation.summary,
                key_reasons=self._blocked_reasons(recommendation.scenarios)
                + self._confidence_reasons(recommendation),
                counterfactuals=[
                    "Giảm giá trị khoản mua, tăng trả trước, hoặc hoãn mua để thỏa ràng buộc."
                ],
            )

        scenario = selected.scenario
        return DecisionExplanation(
            decision_id=decision_id,
            summary=(
                f"Khuyến nghị {scenario.label} vì phương án này thỏa ràng buộc cứng "
                f"và có điểm phù hợp {selected.score:.1f}/100."
            ),
            key_reasons=[
                f"Số dư thấp nhất sau mô phỏng là {scenario.metrics.min_balance} VND.",
                f"DTI tối đa sau mua là {scenario.metrics.max_dti:.1f}%.",
                f"Quỹ khẩn cấp sau quyết định còn {scenario.metrics.efr_after:.1f} tháng.",
            ] + self._confidence_reasons(recommendation),
            counterfactuals=self._counterfactuals(recommendation.scenarios, selected),
        )

    def _confidence_reasons(self, recommendation: RecommendationResult) -> list[str]:
        if "LOW_CONFIDENCE_OBLIGATION" not in recommendation.advisories:
            return []
        names = recommendation.low_confidence_obligations
        if names:
            joined = ", ".join(names)
            return [
                f"Độ tin cậy của quyết định bị giảm vì nghĩa vụ {joined} được suy luận "
                "từ NOTE giao dịch và chưa được xác minh. Hãy xác minh trước khi quyết định."
            ]
        return [
            "Độ tin cậy của quyết định bị giảm vì có nghĩa vụ suy luận từ NOTE giao "
            "dịch chưa được xác minh. Hãy xác minh trước khi quyết định."
        ]

    def _blocked_reasons(self, decisions: list[ScenarioDecision]) -> list[str]:
        reasons: list[str] = []
        for decision in decisions:
            if decision.blocked:
                reasons.append(
                    f"{decision.scenario.label}: {', '.join(decision.reason_codes)}"
                )
        return reasons[:5]

    def _counterfactuals(
        self,
        decisions: list[ScenarioDecision],
        selected: ScenarioDecision,
    ) -> list[str]:
        blocked = [d for d in decisions if d.blocked]
        facts = [
            f"{d.scenario.label} chưa được khuyến nghị vì {', '.join(d.reason_codes)}."
            for d in blocked[:3]
        ]
        lower_payment = [
            d for d in decisions
            if not d.blocked and d.scenario.monthly_payment < selected.scenario.monthly_payment
        ]
        if lower_payment:
            best_lower = sorted(lower_payment, key=lambda d: d.score, reverse=True)[0]
            facts.append(
                f"Có thể chọn {best_lower.scenario.label} nếu ưu tiên trả hàng tháng thấp hơn, "
                f"nhưng điểm phù hợp là {best_lower.score:.1f}/100."
            )
        return facts
