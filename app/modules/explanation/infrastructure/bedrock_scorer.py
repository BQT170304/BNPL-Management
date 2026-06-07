# app/modules/explanation/infrastructure/bedrock_scorer.py
from __future__ import annotations

import json
import logging
from typing import Any, Protocol

from pydantic import ValidationError

from app.modules.advisory.application.dto import (
    OptionScore,
    ScoringPacket,
    ScoringResult,
)
from app.modules.advisory.application.ports import RiskScorer
from app.modules.explanation.schemas import LLMScoringResponse

logger = logging.getLogger(__name__)

_SYSTEM = (
    "Bạn là cố vấn tài chính cá nhân. Dựa trên các chỉ số ĐÃ TÍNH SẴN cho mỗi phương án "
    "thanh toán BNPL, hãy: (1) chấm điểm RỦI RO mỗi phương án 0–100 (0=an toàn nhất), "
    "(2) chọn phương án tốt nhất, (3) viết giải thích 2-3 câu tiếng Việt thông thường, dễ hiểu với người bình thường. "
    "KHÔNG dùng thuật ngữ tài chính chuyên môn hay chữ viết tắt (không dùng DTI, NCF, EFR, delta_pgrs, v.v.). "
    "Thay vào đó dùng: 'tiền còn lại mỗi tháng' thay cho NCF, 'tỷ lệ nợ so với thu nhập' thay cho DTI, "
    "'quỹ dự phòng' thay cho EFR. Nêu cụ thể con số bằng tiền. "
    "QUAN TRỌNG về phương án trả 1 lần (pay_in_full): "
    "chỉ tháng mua bị trừ toàn bộ số tiền (dùng purchase_month_cashflow), "
    "các tháng sau trở lại bình thường (dùng cashflow_after_purchase_month). "
    "Nếu purchase_month_cashflow âm thì phải nói rõ 'cần dùng quỹ dự phòng tháng đó'. "
    "KHÔNG nói 'tiền còn lại không đổi' hay 'không ảnh hưởng' với phương án trả 1 lần. "
    "CHỈ trả về JSON đúng schema, không thêm gì khác."
)


class BedrockClient(Protocol):
    def invoke_model(self, **kwargs: Any) -> Any: ...


def _build_prompt(packet: ScoringPacket) -> str:
    from app.modules.advisory.domain.options import PlanType

    options = []
    for o in packet.options:
        is_full = o.option.type == PlanType.PAY_IN_FULL
        opt: dict = {
            "option_id": o.option.id,
            "label": o.option.label,
            "payment_type": "pay_in_full" if is_full else "installment",
            "monthly_payment": o.payment,
            "total_interest": o.total_interest,
            "dti_new": round(o.dti_new, 2),
            "efr_after": round(o.efr_after, 2),
            "efr_safety": o.efr_safety,
            "delta_pgrs": round(o.delta_pgrs, 2),
            "flags": o.flags,
        }
        if is_full:
            # One-time hit in the purchase month, then back to normal.
            opt["upfront_payment"] = o.option.upfront
            opt["purchase_month_cashflow"] = packet.current_ncf - o.option.upfront
            opt["cashflow_after_purchase_month"] = packet.current_ncf
            opt["note"] = (
                "Trả 1 lần: chỉ tháng mua bị trừ trọn số tiền (tiền còn lại tháng đó "
                f"= {packet.current_ncf - o.option.upfront:,.0f}đ, có thể âm phải lấy từ quỹ dự phòng); "
                "từ tháng sau dòng tiền trở lại bình thường, không phải trả góp."
            )
        else:
            # Recurring monthly payment for the whole term.
            opt["ncf_new"] = o.ncf_new
            opt["ncf_change"] = o.ncf_new - packet.current_ncf
        if o.goal_impacts:
            opt["goal_impacts"] = [
                {
                    "goal": gi.name,
                    "delay_months": round(gi.delay_months, 1),
                    "reachable_by_deadline": gi.reachable_by_deadline,
                    "monthly_shortfall": gi.monthly_shortfall,
                }
                for gi in o.goal_impacts
            ]
        options.append(opt)

    payload = {
        "item": packet.item_name,
        "amount": packet.purchase_amount,
        "risk_tolerance": packet.risk_tolerance,
        "current_profile": {
            "ncf": packet.current_ncf,
            "dti": round(packet.current_dti, 2),
            "efr": round(packet.current_efr, 2),
            "pgrs": round(packet.current_pgrs, 2),
        },
        "options": options,
        "response_schema": {
            "options": [
                {
                    "option_id": "str",
                    "risk_score": "0-100 (0=safest)",
                    "recommended": "bool",
                    "explanation": (
                        "2-3 câu tiếng Việt đơn giản. Với phương án trả 1 lần: nói rõ tháng mua "
                        "bị trừ trọn số tiền (nêu tiền còn lại tháng đó, nếu âm thì phải dùng quỹ dự phòng), "
                        "các tháng sau trở lại bình thường. Với trả góp: nêu tiền trả mỗi tháng và "
                        "tiền còn lại mỗi tháng trong suốt kỳ. Không dùng DTI/NCF/EFR."
                    ),
                    "key_factors": ["str"],
                }
            ],
            "best_option_id": "str",
            "summary": "1 câu tiếng Việt tổng kết",
        },
    }
    return json.dumps(payload, ensure_ascii=False)


class BedrockScorer(RiskScorer):
    def __init__(self, client: BedrockClient, model_id: str, fallback: RiskScorer) -> None:
        self._client = client
        self._model_id = model_id
        self._fallback = fallback

    def score(self, packet: ScoringPacket) -> ScoringResult:
        try:
            text = self._invoke(packet)
            parsed = LLMScoringResponse.model_validate_json(text)
        except (ValidationError, json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.warning("Bedrock response unusable, falling back: %s", exc)
            return self._fallback.score(packet)
        except Exception as exc:  # boto3 ClientError etc.
            logger.warning("Bedrock call failed, falling back: %s", exc)
            return self._fallback.score(packet)

        return ScoringResult(
            options=[
                OptionScore(o.option_id, o.risk_score, o.recommended,
                            o.explanation, o.key_factors)
                for o in parsed.options
            ],
            best_option_id=parsed.best_option_id,
            summary=parsed.summary,
            scorer_used="bedrock",
        )

    def _invoke(self, packet: ScoringPacket) -> str:
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "system": _SYSTEM,
            "messages": [{"role": "user", "content": _build_prompt(packet)}],
        })
        response = self._client.invoke_model(modelId=self._model_id, body=body)
        raw = json.loads(response["body"].read())
        return str(raw["content"][0]["text"])
