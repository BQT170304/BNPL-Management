"""Translate a computed EvaluationResult into plain Vietnamese for non-technical users.

Calls the hosted LLM if available; falls back to a template-based generator.
"""
from __future__ import annotations

import json
import logging
import math
import urllib.request
from dataclasses import dataclass
from typing import Any

from app.modules.advisory.application.dto import OptionPacket
from app.modules.advisory.application.services import EvaluationResult
from app.modules.analysis.domain.results import ProfileMetrics

logger = logging.getLogger(__name__)


@dataclass
class ExplanationResult:
    payment_recommendation: str
    goal_delay_summary: str
    emergency_fund_assessment: str
    balanced_option_summary: str
    source: str   # "llm" | "template"


@dataclass
class HomeAdviceResult:
    advice: str
    scorer_used: str   # "llm" | "template"


_SYSTEM = """\
Bạn là cố vấn tài chính cá nhân. Hãy giải thích bằng tiếng Việt đơn giản, thân thiện \
— không dùng thuật ngữ tài chính phức tạp, không liệt kê số chỉ số thô. \
Mỗi câu trả lời 2-3 câu ngắn gọn.
"""

_RESPONSE_SCHEMA = """\
{
  "payment_recommendation": "...",
  "goal_delay_summary": "...",
  "emergency_fund_assessment": "...",
  "balanced_option_summary": "..."
}
"""

_USER_PROMPT = """\
Dựa trên thông tin trên, hãy trả lời bằng tiếng Việt tự nhiên:

1. Tôi nên trả thẳng hay trả góp? Nếu trả góp thì mấy tháng là tối ưu?
2. Quyết định này khiến tôi chậm đạt các mục tiêu bao lâu?
3. Nó ăn vào quỹ khẩn cấp bao nhiêu? Tôi còn an toàn không?
4. Trong tất cả các phương án, đâu là lựa chọn cân bằng nhất giữa nhu cầu hiện tại và tương lai?

Trả về JSON theo schema sau (không thêm gì khác):
""" + _RESPONSE_SCHEMA


def _build_facts(result: EvaluationResult) -> str:
    lines: list[str] = []
    lines.append(f"Thu nhập ròng hiện tại: {result.metrics.ncf:,.0f} đ/tháng")
    lines.append(f"Quỹ khẩn cấp hiện tại: {result.metrics.efr:.1f} tháng chi tiêu thiết yếu")
    lines.append(f"DTI hiện tại: {result.metrics.dti:.0f}%")
    lines.append("")

    blocked = {"NEGATIVE_CASHFLOW", "REQUIRES_EMERGENCY_FUND"}
    for p in result.packets:
        label = p.option.label
        if any(f in blocked for f in p.flags):
            lines.append(f"{label}: không khả thi ({', '.join(p.flags)})")
            continue
        lines.append(f"{label}:")
        if p.payment:
            lines.append(f"  - Thanh toán: {p.payment:,.0f} đ/tháng")
        else:
            lines.append(f"  - Trả 1 lần: {p.option.upfront:,.0f} đ")
        lines.append(f"  - Dòng tiền còn lại: {p.ncf_new:,.0f} đ/tháng")
        lines.append(f"  - Quỹ khẩn cấp sau khi mua: {p.efr_after:.1f} tháng ({p.efr_safety})")
        lines.append(f"  - Tổng lãi phải trả: {p.total_interest:,.0f} đ")
        delayed = [gi for gi in p.goal_impacts
                   if gi.delay_months > 0 and not math.isinf(gi.delay_months)]
        if delayed:
            delay_strs = [f"'{gi.name}' chậm {gi.delay_months:.0f} tháng" for gi in delayed]
            lines.append(f"  - Ảnh hưởng mục tiêu: {', '.join(delay_strs)}")
        else:
            lines.append("  - Không làm chậm mục tiêu nào")

    lines.append("")
    lines.append(f"Phân tích cân bằng (hệ thống): {result.scoring.balance_recommendation}")
    return "\n".join(lines)


class ExplainService:
    def __init__(
        self,
        llm_url: str = "",
        llm_auth: str = "",
        llm_model: str = "Qwen3-14B",
        llm_enabled: bool = False,
    ) -> None:
        self._url = llm_url
        self._auth = llm_auth
        self._model = llm_model
        self._llm_enabled = llm_enabled

    def explain(self, result: EvaluationResult) -> ExplanationResult:
        facts = _build_facts(result)
        if self._llm_enabled and self._url:
            try:
                return self._explain_via_llm(facts)
            except Exception as exc:
                logger.warning("LLM explain failed, using template: %s", exc)
        return self._explain_via_template(result)

    def _explain_via_llm(self, facts: str) -> ExplanationResult:
        body = json.dumps({
            "model": self._model,
            "max_tokens": 1500,
            "temperature": 0.3,
            "chat_template_kwargs": {"enable_thinking": False},
            "messages": [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": facts + "\n\n" + _USER_PROMPT},
            ],
        }, ensure_ascii=False).encode()

        req = urllib.request.Request(
            self._url, data=body, method="POST",
            headers={"Content-Type": "application/json", "Authorization": self._auth},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw: dict[str, Any] = json.loads(resp.read())

        parsed = json.loads(raw["choices"][0]["message"]["content"])
        return ExplanationResult(
            payment_recommendation=parsed["payment_recommendation"],
            goal_delay_summary=parsed["goal_delay_summary"],
            emergency_fund_assessment=parsed["emergency_fund_assessment"],
            balanced_option_summary=parsed["balanced_option_summary"],
            source="llm",
        )

    # ── Home dashboard advice ─────────────────────────────────────────────────

    def advise_home(self, metrics: ProfileMetrics) -> HomeAdviceResult:
        """Generate a brief financial health summary for the home dashboard."""
        if self._llm_enabled and self._url:
            try:
                return self._home_via_llm(metrics)
            except Exception as exc:
                logger.warning("LLM home advice failed, using template: %s", exc)
        return HomeAdviceResult(advice=_home_template(metrics), scorer_used="template")

    def _home_via_llm(self, metrics: ProfileMetrics) -> HomeAdviceResult:
        facts = (
            f"Điểm sức khoẻ tài chính: {metrics.overall_health_score}/100\n"
            f"Dòng tiền ròng: {metrics.ncf:,.0f} đ/tháng\n"
            f"Tỷ lệ nợ/thu nhập (DTI): {metrics.dti:.1f}%\n"
            f"Tỷ lệ tiết kiệm: {metrics.saving_rate:.1f}%\n"
            f"Quỹ khẩn cấp: {metrics.efr:.1f} tháng\n"
            f"Số mục tiêu tài chính: {len(metrics.goals)}\n"
            f"Cảnh báo hệ thống: {', '.join(metrics.flags) if metrics.flags else 'Không có'}\n"
        )
        prompt = (
            facts + "\n"
            "Hãy đưa ra nhận xét ngắn gọn (2-3 câu) về tình trạng tài chính và "
            "1-2 hành động cụ thể để cải thiện. Viết bằng tiếng Việt, thân thiện, dễ hiểu. "
            "Chỉ trả về đoạn văn, không JSON, không bullet point."
        )
        body = json.dumps({
            "model": self._model,
            "max_tokens": 300,
            "temperature": 0.4,
            "chat_template_kwargs": {"enable_thinking": False},
            "messages": [
                {"role": "system", "content": "Bạn là cố vấn tài chính cá nhân thân thiện, trả lời bằng tiếng Việt ngắn gọn."},
                {"role": "user", "content": prompt},
            ],
        }, ensure_ascii=False).encode()
        req = urllib.request.Request(
            self._url, data=body, method="POST",
            headers={"Content-Type": "application/json", "Authorization": self._auth},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw: dict[str, Any] = json.loads(resp.read())
        advice = str(raw["choices"][0]["message"]["content"]).strip()
        return HomeAdviceResult(advice=advice, scorer_used="llm")

    def _explain_via_template(self, result: EvaluationResult) -> ExplanationResult:
        best_id = result.scoring.best_option_id
        best = next((p for p in result.packets if p.option.id == best_id), result.packets[0])
        blocked = {"NEGATIVE_CASHFLOW", "REQUIRES_EMERGENCY_FUND"}
        viable = [p for p in result.packets if not any(f in blocked for f in p.flags)]

        payment_rec = _payment_recommendation(best, viable)
        goal_delay = _goal_delay_summary(best)
        efr_assessment = _emergency_fund_assessment(best)
        balance = result.scoring.balance_recommendation

        return ExplanationResult(
            payment_recommendation=payment_rec,
            goal_delay_summary=goal_delay,
            emergency_fund_assessment=efr_assessment,
            balanced_option_summary=balance,
            source="template",
        )


def _payment_recommendation(best: OptionPacket, viable: list[OptionPacket]) -> str:
    from app.modules.advisory.domain.options import PlanType
    if not viable:
        return ("Hiện tại chưa có phương án BNPL nào an toàn với ngân sách của bạn. "
                "Khuyến nghị chờ đến khi dòng tiền ổn định hơn hoặc chọn sản phẩm có giá thấp hơn.")
    if best.option.type == PlanType.PAY_IN_FULL:
        return ("Trả thẳng 1 lần là tối ưu nhất — không mất thêm lãi và giải phóng dòng tiền "
                "ngay từ tháng sau.")
    months = best.option.months or 0
    return (f"Trả góp {months} tháng phù hợp nhất với ngân sách của bạn — "
            f"mỗi tháng bỏ ra {best.payment:,.0f} đ, "
            f"dòng tiền vẫn còn {best.ncf_new:,.0f} đ dư sau khi trả.")


def _goal_delay_summary(best: OptionPacket) -> str:
    finite_delays = [gi for gi in best.goal_impacts
                     if gi.delay_months > 0 and not math.isinf(gi.delay_months)]
    if not finite_delays:
        return ("Phương án được chọn không làm chậm bất kỳ mục tiêu nào của bạn — "
                "kế hoạch tiết kiệm vẫn đi đúng lộ trình.")

    parts = [f"'{gi.name}' trễ khoảng {gi.delay_months:.0f} tháng" for gi in finite_delays[:3]]
    summary = "Quyết định này ảnh hưởng đến: " + ", ".join(parts) + ". "

    unreachable = [gi for gi in best.goal_impacts if not gi.reachable_by_deadline]
    if unreachable:
        names = ", ".join(f"'{gi.name}'" for gi in unreachable)
        summary += (f"Các mục tiêu {names} có thể không kịp đúng hạn — "
                    "nên điều chỉnh deadline hoặc tăng tiết kiệm hàng tháng.")
    return summary


def _emergency_fund_assessment(best: OptionPacket) -> str:
    efr = best.efr_after
    if best.efr_safety == "SAFE":
        return (f"Quỹ khẩn cấp vẫn còn {efr:.1f} tháng chi tiêu thiết yếu — "
                "đây là mức an toàn (ngưỡng tối thiểu là 3 tháng). Bạn vẫn ổn.")
    if best.efr_safety == "WARNING":
        return (f"Sau khi mua, quỹ khẩn cấp còn {efr:.1f} tháng — dưới mức khuyến nghị 3 tháng. "
                "Không nguy hiểm ngay nhưng nên ưu tiên bổ sung quỹ này trước khi chi tiêu lớn tiếp theo.")
    return (f"Cảnh báo: quỹ khẩn cấp chỉ còn {efr:.1f} tháng — rất mỏng. "
            "Nếu có sự cố bất ngờ (mất việc, bệnh viện), bạn sẽ không có đệm an toàn. "
            "Hãy cân nhắc kỹ trước khi quyết định.")


def _home_template(metrics: ProfileMetrics) -> str:
    parts: list[str] = []
    score = metrics.overall_health_score
    if score >= 70:
        parts.append("Tài chính của bạn đang ở trạng thái tốt.")
    elif score >= 50:
        parts.append("Tài chính ổn định nhưng có một vài điểm cần chú ý.")
    else:
        parts.append("Tài chính đang ở mức cần cải thiện, có một số rủi ro cần xử lý.")

    if metrics.ncf < 0:
        parts.append("Dòng tiền tháng đang âm — cần cắt giảm chi tiêu hoặc tăng thu nhập.")
    elif metrics.saving_rate < 10:
        parts.append(f"Tỷ lệ tiết kiệm chỉ đạt {metrics.saving_rate:.0f}%, nên hướng đến ít nhất 20% thu nhập.")
    if metrics.efr < 3:
        parts.append(f"Quỹ khẩn cấp còn {metrics.efr:.1f} tháng — cần bổ sung để đạt 3–6 tháng chi tiêu.")
    if metrics.dti > 40:
        parts.append(f"Tỷ lệ nợ/thu nhập ở mức {metrics.dti:.0f}%, hạn chế vay thêm cho đến khi giảm xuống dưới 40%.")

    return " ".join(parts) if parts else "Không có dữ liệu đủ để phân tích."
