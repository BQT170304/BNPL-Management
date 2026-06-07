"""Risk scorer that calls OpenRouter (OpenAI-compatible API).

Configure via env:
  OPENROUTER_ENABLED=true
  OPENROUTER_API_KEY=sk-or-v1-...
  OPENROUTER_MODEL=qwen/qwen3-14b          # or any model on openrouter.ai
"""
from __future__ import annotations

import json
import logging
import urllib.request
from typing import Any

from pydantic import ValidationError

from app.modules.advisory.application.dto import OptionScore, ScoringPacket, ScoringResult
from app.modules.advisory.application.ports import RiskScorer
from app.modules.explanation.infrastructure.bedrock_scorer import _build_prompt
from app.modules.explanation.schemas import LLMScoringResponse

logger = logging.getLogger(__name__)

_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

_SYSTEM = (
    "Bạn là cố vấn tài chính cá nhân. Dựa trên các chỉ số tài chính đã tính sẵn "
    "cho mỗi phương án thanh toán BNPL, hãy chấm điểm RỦI RO (0–100, 0=an toàn nhất) "
    "cho từng phương án và chọn phương án tốt nhất. "
    "Viết explanation 2-3 câu tiếng Việt thông thường, dễ hiểu với người bình thường — "
    "KHÔNG dùng từ viết tắt (DTI, NCF, EFR, delta_pgrs). "
    "Dùng: 'tiền còn lại mỗi tháng' thay cho NCF, 'tỷ lệ nợ' thay cho DTI, 'quỹ dự phòng' thay cho EFR. "
    "Nêu con số cụ thể bằng tiền (ví dụ: mỗi tháng trả 2 triệu, sau đó còn lại 3 triệu). "
    "Trả về JSON đúng schema, không thêm chữ nào khác."
)


class OpenRouterScorer:
    """Calls OpenRouter API for risk scoring, falls back on any error."""

    def __init__(self, api_key: str, model: str, fallback: RiskScorer) -> None:
        self._api_key = api_key
        self._model = model
        self._fallback = fallback

    def score(self, packet: ScoringPacket) -> ScoringResult:
        try:
            text = self._invoke(packet)
            parsed = LLMScoringResponse.model_validate_json(text)
        except (ValidationError, json.JSONDecodeError, KeyError) as exc:
            logger.warning("OpenRouter response unusable, falling back: %s", exc)
            return self._fallback.score(packet)
        except Exception as exc:
            logger.warning("OpenRouter call failed, falling back: %s", exc)
            return self._fallback.score(packet)

        return ScoringResult(
            options=[
                OptionScore(o.option_id, o.risk_score, o.recommended,
                            o.explanation, o.key_factors)
                for o in parsed.options
            ],
            best_option_id=parsed.best_option_id,
            summary=parsed.summary,
            scorer_used="openrouter",
        )

    def _invoke(self, packet: ScoringPacket) -> str:
        body = json.dumps({
            "model": self._model,
            "max_tokens": 2000,
            "temperature": 0.1,
            "messages": [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": _build_prompt(packet)},
            ],
        }, ensure_ascii=False).encode()

        req = urllib.request.Request(
            _OPENROUTER_URL,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
                "HTTP-Referer": "https://d2ttyqgmp7bw35.cloudfront.net",
                "X-Title": "BNPL Assistant",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw: dict[str, Any] = json.loads(resp.read())

        content = raw["choices"][0]["message"]["content"]
        # Strip markdown code fences if model wraps JSON in ```json ... ```
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return content.strip()
