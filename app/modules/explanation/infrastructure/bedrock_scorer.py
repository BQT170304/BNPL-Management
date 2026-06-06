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
    "Bạn là cố vấn tài chính. Dựa trên các chỉ số ĐÃ TÍNH SẴN cho mỗi phương án "
    "thanh toán, hãy chấm điểm RỦI RO mỗi phương án trên thang 0-100 "
    "(0 = an toàn nhất, 100 = rủi ro nhất) và chọn phương án tốt nhất "
    "(rủi ro thấp nhất, không vi phạm ràng buộc cứng). "
    "CHỈ trả về JSON đúng schema, không thêm chữ nào khác."
)


class BedrockClient(Protocol):
    def invoke_model(self, **kwargs: Any) -> Any: ...


def _build_prompt(packet: ScoringPacket) -> str:
    options = [
        {
            "option_id": o.option.id, "label": o.option.label,
            "monthly_payment": o.payment, "ncf_new": o.ncf_new,
            "dti_new": round(o.dti_new, 2), "efr_after": round(o.efr_after, 2),
            "delta_pgrs": round(o.delta_pgrs, 2),
            "subscores": {
                "cashflow": o.subscores.cashflow, "goal": o.subscores.goal,
                "efr": o.subscores.efr, "dti": o.subscores.dti,
            },
            "flags": o.flags,
        }
        for o in packet.options
    ]
    payload = {
        "item": packet.item_name, "amount": packet.purchase_amount,
        "risk_tolerance": packet.risk_tolerance,
        "current": {
            "ncf": packet.current_ncf, "dti": round(packet.current_dti, 2),
            "efr": round(packet.current_efr, 2), "pgrs": round(packet.current_pgrs, 2),
        },
        "options": options,
        "response_schema": {
            "options": [{"option_id": "str", "risk_score": "0-100",
                         "recommended": "bool", "explanation": "str",
                         "key_factors": ["str"]}],
            "best_option_id": "str", "summary": "str",
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
