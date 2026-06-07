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
    "'quỹ dự phòng' thay cho EFR. Nêu cụ thể con số bằng tiền (ví dụ: còn lại 2 triệu/tháng, lãi phát sinh 1.5 triệu). "
    "CHỈ trả về JSON đúng schema, không thêm gì khác."
)


class BedrockClient(Protocol):
    def invoke_model(self, **kwargs: Any) -> Any: ...


def _build_prompt(packet: ScoringPacket) -> str:
    options = []
    for o in packet.options:
        opt: dict = {
            "option_id": o.option.id,
            "label": o.option.label,
            "monthly_payment": o.payment,
            "total_interest": o.total_interest,
            "ncf_new": o.ncf_new,
            "ncf_change": o.ncf_new - packet.current_ncf,
            "dti_new": round(o.dti_new, 2),
            "efr_after": round(o.efr_after, 2),
            "efr_safety": o.efr_safety,
            "delta_pgrs": round(o.delta_pgrs, 2),
            "flags": o.flags,
        }
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
                    "explanation": "2-3 câu tiếng Việt đơn giản: nêu tiền trả mỗi tháng, lãi phát sinh, tiền còn lại — không dùng DTI/NCF/EFR",
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
