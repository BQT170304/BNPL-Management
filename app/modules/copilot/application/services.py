from __future__ import annotations

from app.modules.analysis.application.services import AnalysisService
from app.modules.analysis.domain.alerts import check_alerts
from app.modules.copilot.application.ports import Narrator
from app.modules.copilot.domain.intents import CopilotTool, ParsedIntent, parse_intent
from app.modules.copilot.domain.reply import CopilotReply
from app.modules.decisions.application.services import DecisionService
from app.modules.forecasting.application.services import ForecastService
from app.modules.forecasting.domain.warnings import forecast_alerts
from app.modules.obligations.application.services import ObligationService
from app.modules.planning.application.optimizer import ConstraintOptimizer
from app.modules.profiles.application.ports import ProfileRepository


class CopilotService:
    """Conversational layer that only calls deterministic tools.

    The LLM (if any) is used solely to narrate an already-computed result. No
    risk score, approval, or recommendation is ever produced by the LLM.
    """

    def __init__(
        self,
        profiles: ProfileRepository,
        optimizer: ConstraintOptimizer,
        decisions: DecisionService,
        forecast: ForecastService,
        analysis: AnalysisService,
        obligations: ObligationService,
        narrator: Narrator | None = None,
        efr_safe_months: int = 3,
    ) -> None:
        self._profiles = profiles
        self._optimizer = optimizer
        self._decisions = decisions
        self._forecast = forecast
        self._analysis = analysis
        self._obligations = obligations
        self._narrator = narrator
        self._efr_safe_months = efr_safe_months

    async def chat(
        self,
        message: str,
        profile_id: str | None = None,
        decision_id: str | None = None,
    ) -> CopilotReply:
        intent = parse_intent(message)
        if intent.tool == CopilotTool.EXPLAIN:
            reply = await self._handle_explain(decision_id)
        elif intent.tool == CopilotTool.RECOMMEND:
            reply = await self._handle_recommend(message, profile_id, intent)
        elif intent.tool == CopilotTool.FORECAST:
            reply = await self._handle_forecast(profile_id)
        elif intent.tool == CopilotTool.ALERTS:
            reply = await self._handle_alerts(profile_id)
        elif intent.tool == CopilotTool.OBLIGATIONS:
            reply = await self._handle_obligations(profile_id)
        else:
            reply = self._clarify(
                "Mình có thể giúp mô phỏng khoản mua, xem dự báo dòng tiền, cảnh báo, "
                "nghĩa vụ, hoặc giải thích một quyết định. Bạn muốn hỏi gì?"
            )
        return self._narrated(reply)

    def _narrated(self, reply: CopilotReply) -> CopilotReply:
        if self._narrator is None:
            return reply
        narrated = self._narrator.narrate(reply.reply, reply.data)
        # Narration only rephrases text; the decision/flags are unchanged.
        return CopilotReply(
            reply=narrated,
            tool=reply.tool,
            used_optimizer=reply.used_optimizer,
            decision_id=reply.decision_id,
            follow_up=reply.follow_up,
            data=reply.data,
        )

    def _clarify(self, question: str) -> CopilotReply:
        return CopilotReply(
            reply=question,
            tool=CopilotTool.CLARIFY,
            used_optimizer=False,
            decision_id=None,
            follow_up=question,
            data={},
        )

    async def _handle_recommend(
        self,
        message: str,
        profile_id: str | None,
        intent: ParsedIntent,
    ) -> CopilotReply:
        # Guardrail: never approve without running the optimizer. If we cannot
        # run it, ask for the missing input instead of inventing an answer.
        if not profile_id:
            return self._clarify(
                "Bạn cho mình biết hồ sơ (profile_id) để mình mô phỏng khoản mua nhé?"
            )
        if intent.amount is None:
            return self._clarify("Khoản mua trị giá bao nhiêu để mình mô phỏng?")

        profile = await self._profiles.get(profile_id)
        result = await self._optimizer.recommend(
            profile,
            item_name=intent.item_name,
            amount=intent.amount,
            tenor=intent.months,
        )
        trace = await self._decisions.record(
            result,
            input_snapshot={
                "source": "copilot",
                "message": message,
                "profile_id": profile_id,
                "amount": intent.amount,
                "tenor": intent.months,
            },
        )
        best = next((d for d in result.scenarios if d.recommended), None)
        if best is not None:
            draft = (
                f"Với khoản mua {intent.item_name} {intent.amount:,}đ, phương án phù hợp "
                f"nhất là {best.scenario.label} (điểm {best.score:.1f}/100, "
                f"trả {best.scenario.monthly_payment:,}đ/tháng, "
                f"tổng chi phí {best.scenario.cost.total_cost:,}đ)."
            )
        else:
            draft = (
                f"Khoản mua {intent.item_name} {intent.amount:,}đ chưa có phương án nào "
                "thỏa ràng buộc an toàn (số dư, DTI, quỹ khẩn cấp). Nên giảm giá trị, "
                "tăng trả trước hoặc hoãn mua."
            )
        if result.advisories:
            draft += " Lưu ý: có nghĩa vụ suy luận từ NOTE cần xác minh trước khi quyết định."
        return CopilotReply(
            reply=draft,
            tool=CopilotTool.RECOMMEND,
            used_optimizer=True,
            decision_id=trace.id,
            follow_up=f"Bạn muốn mình giải thích chi tiết quyết định {trace.id} không?",
            data={
                "best_scenario_id": result.best_scenario_id,
                "advisories": result.advisories,
                "min_confidence": result.min_confidence,
            },
        )

    async def _handle_explain(self, decision_id: str | None) -> CopilotReply:
        if not decision_id:
            return self._clarify(
                "Bạn cho mình mã quyết định (decision_id) để giải thích nhé?"
            )
        explanation = await self._decisions.explain(decision_id)
        draft = explanation.summary
        if explanation.key_reasons:
            draft += " Lý do chính: " + " ".join(explanation.key_reasons)
        return CopilotReply(
            reply=draft,
            tool=CopilotTool.EXPLAIN,
            used_optimizer=False,
            decision_id=decision_id,
            follow_up=None,
            data={
                "key_reasons": explanation.key_reasons,
                "counterfactuals": explanation.counterfactuals,
            },
        )

    async def _handle_forecast(self, profile_id: str | None) -> CopilotReply:
        if not profile_id:
            return self._clarify("Bạn cho mình biết hồ sơ (profile_id) để xem dự báo nhé?")
        profile = await self._profiles.get(profile_id)
        result = await self._forecast.forecast(profile, months=6)
        summary = result.summary
        draft = (
            f"Dự báo dòng tiền: 30 ngày tới {summary.next_30_net:,}đ, "
            f"90 ngày tới {summary.next_90_net:,}đ, số dư thấp nhất dự kiến "
            f"{summary.min_projected_balance:,}đ."
        )
        if summary.min_projected_balance < 0:
            draft += " Cảnh báo: số dư có thể âm trong kỳ dự báo."
        return CopilotReply(
            reply=draft,
            tool=CopilotTool.FORECAST,
            used_optimizer=False,
            decision_id=None,
            follow_up=None,
            data={
                "next_30_net": summary.next_30_net,
                "next_90_net": summary.next_90_net,
                "min_projected_balance": summary.min_projected_balance,
            },
        )

    async def _handle_alerts(self, profile_id: str | None) -> CopilotReply:
        if not profile_id:
            return self._clarify("Bạn cho mình biết hồ sơ (profile_id) để xem cảnh báo nhé?")
        profile = await self._profiles.get(profile_id)
        alerts = [a.message for a in check_alerts(self._analysis.analyze(profile))]
        forecast = await self._forecast.forecast(profile, months=6)
        alerts += [
            a.message
            for a in forecast_alerts(forecast, profile, safe_months=self._efr_safe_months)
        ]
        if alerts:
            draft = "Cảnh báo hiện tại: " + " ".join(alerts)
        else:
            draft = "Hiện chưa có cảnh báo tài chính nào."
        return CopilotReply(
            reply=draft,
            tool=CopilotTool.ALERTS,
            used_optimizer=False,
            decision_id=None,
            follow_up=None,
            data={"alerts": alerts},
        )

    async def _handle_obligations(self, profile_id: str | None) -> CopilotReply:
        if not profile_id:
            return self._clarify("Bạn cho mình biết hồ sơ (profile_id) để xem nghĩa vụ nhé?")
        obligations = await self._obligations.list_by_profile(profile_id)
        total_monthly = sum(o.monthly_payment for o in obligations)
        unverified = [o.merchant for o in obligations if not o.verified and o.confidence < 1.0]
        draft = (
            f"Bạn đang có {len(obligations)} nghĩa vụ, tổng trả {total_monthly:,}đ/tháng."
        )
        if unverified:
            draft += " Cần xác minh: " + ", ".join(unverified) + "."
        return CopilotReply(
            reply=draft,
            tool=CopilotTool.OBLIGATIONS,
            used_optimizer=False,
            decision_id=None,
            follow_up=None,
            data={"count": len(obligations), "unverified": unverified},
        )
