"""Risk scorer that calls a locally-hosted OpenAI-compatible LLM (e.g. Qwen3-14B).

Configure via env:
  LOCAL_LLM_URL=http://203.113.152.4:7777/llm/v1/chat/completions
  LOCAL_LLM_AUTH=Basic dmlldHRlbF9haTpWYWlAMjAyNQ==
  LOCAL_LLM_MODEL=Qwen3-14B
"""
from __future__ import annotations

import json
import logging
import urllib.request
from typing import Any

from pydantic import ValidationError

from app.modules.advisory.application.dto import (
    OptionScore,
    ScoringPacket,
    ScoringResult,
)
from app.modules.advisory.application.ports import RiskScorer
from app.modules.explanation.infrastructure.bedrock_scorer import _build_prompt
from app.modules.explanation.schemas import LLMScoringResponse

logger = logging.getLogger(__name__)

_SYSTEM = (
    "Bạn là cố vấn tài chính cá nhân. Dựa trên các chỉ số tài chính đã tính sẵn "
    "cho mỗi phương án thanh toán BNPL, hãy chấm điểm RỦI RO (0–100, 0=an toàn nhất) "
    "cho từng phương án và chọn phương án tốt nhất. "
    "Viết explanation 2-3 câu tiếng Việt thông thường, dễ hiểu với người bình thường — "
    "KHÔNG dùng từ viết tắt (DTI, NCF, EFR, delta_pgrs, v.v.). "
    "Dùng: 'tiền còn lại mỗi tháng' thay cho NCF, 'tỷ lệ nợ' thay cho DTI, 'quỹ dự phòng' thay cho EFR. "
    "Nêu con số cụ thể bằng tiền (ví dụ: mỗi tháng trả 2 triệu, sau đó còn lại 3 triệu). "
    "Trả về JSON đúng schema, không thêm chữ nào khác."
)


class LocalLLMScorer:
    """Calls a locally-hosted OpenAI-compatible endpoint for risk scoring."""

    def __init__(self, url: str, auth: str, model: str, fallback: RiskScorer) -> None:
        self._url = url
        self._auth = auth
        self._model = model
        self._fallback = fallback

    def score(self, packet: ScoringPacket) -> ScoringResult:
        try:
            text = self._invoke(packet)
            parsed = LLMScoringResponse.model_validate_json(text)
        except (ValidationError, json.JSONDecodeError, KeyError) as exc:
            logger.warning("LocalLLM response unusable, falling back: %s", exc)
            return self._fallback.score(packet)
        except Exception as exc:
            logger.warning("LocalLLM call failed, falling back: %s", exc)
            return self._fallback.score(packet)

        return ScoringResult(
            options=[
                OptionScore(o.option_id, o.risk_score, o.recommended,
                            o.explanation, o.key_factors)
                for o in parsed.options
            ],
            best_option_id=parsed.best_option_id,
            summary=parsed.summary,
            scorer_used="local_llm",
        )

    def _invoke(self, packet: ScoringPacket) -> str:
        body = json.dumps({
            "model": self._model,
            "max_tokens": 2000,
            "temperature": 0.1,
            "top_p": 0.8,
            "presence_penalty": 1.5,
            "chat_template_kwargs": {"enable_thinking": False},
            "messages": [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": _build_prompt(packet)},
            ],
        }, ensure_ascii=False).encode()

        req = urllib.request.Request(
            self._url,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": self._auth,
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw: dict[str, Any] = json.loads(resp.read())

        return str(raw["choices"][0]["message"]["content"])
