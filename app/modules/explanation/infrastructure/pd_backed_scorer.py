"""RiskScorer adapter backed by the real PD (Probability of Default) model.

Scores each option by:
1. Checking hard block rules (NEGATIVE_CASHFLOW, REQUIRES_EMERGENCY_FUND) — no weights
2. Computing PD via LogisticRegression trained on Taiwan Credit Card Default data
3. Converting PD → credit score (600 − 20·ln(PD/(1−PD)), clamped 300–850)
4. Converting credit score → risk score (0–100)

Falls back to the injected scorer when the PD model is unavailable.
"""
from __future__ import annotations

import logging

from app.modules.advisory.application.dto import (
    OptionScore,
    ScoringPacket,
    ScoringResult,
)
from app.modules.advisory.application.ports import RiskScorer
from app.modules.ml.application.pd_feature_extractor import PDFeatureExtractor
from app.modules.ml.infrastructure.pd_scorer import PDScorer

logger = logging.getLogger(__name__)

_BLOCKED_FLAGS = {"NEGATIVE_CASHFLOW", "REQUIRES_EMERGENCY_FUND"}

_FACTOR_LABELS = {
    "util_ratio": "tỷ lệ nợ/thu nhập (DTI)",
    "max_dpd": "lịch sử trả nợ",
    "avg_dpd": "hành vi thanh toán trung bình",
    "pay_coverage": "khả năng chi trả",
    "log_limit": "đệm tài chính (quỹ khẩn cấp)",
}


def _shap_factors(pipeline: object, features_list: list[float],
                  feature_names: tuple[str, ...]) -> list[str]:
    try:
        import shap
        import numpy as np
        explainer = shap.LinearExplainer(
            pipeline.named_steps["lr"],  # type: ignore[attr-defined]
            masker=shap.maskers.Independent(
                pipeline.named_steps["scaler"].transform(  # type: ignore[attr-defined]
                    [features_list]
                )
            ),
        )
        vals = explainer.shap_values(
            pipeline.named_steps["scaler"].transform([features_list])  # type: ignore[attr-defined]
        )[0]
        ranked = sorted(zip(feature_names, vals), key=lambda x: abs(x[1]), reverse=True)[:3]
        result = []
        for feat, val in ranked:
            label = _FACTOR_LABELS.get(feat, feat)
            direction = "tăng rủi ro" if val > 0 else "giảm rủi ro"
            result.append(f"{label} ({direction})")
        return result
    except Exception:
        return []


class PDBackedScorer:
    """Scores options with the PD model; falls back to the injected scorer."""

    def __init__(self, pd_scorer: PDScorer, fallback: RiskScorer) -> None:
        self._pd = pd_scorer
        self._fallback = fallback
        self._extractor = PDFeatureExtractor()

    def score(self, packet: ScoringPacket) -> ScoringResult:
        if not self._pd.is_available():
            return self._fallback.score(packet)

        scores: list[OptionScore] = []
        for opt in packet.options:
            try:
                blocked = any(f in _BLOCKED_FLAGS for f in opt.flags)
                features = self._extractor.extract(packet, opt)
                credit_score, risk = self._pd.score_option(features)

                if blocked:
                    risk = max(risk, 85.0)

                pipeline = self._pd._artifact["pipeline"]  # type: ignore[attr-defined]
                factors = _shap_factors(
                    pipeline, features.to_list(), features.FEATURE_NAMES
                )
                explanation = (
                    f"{opt.option.label}: điểm tín dụng {credit_score} "
                    f"(rủi ro {risk:.1f}/100)"
                    + (" — không khuyến nghị" if blocked else "")
                )
                scores.append(OptionScore(
                    option_id=opt.option.id,
                    risk_score=round(risk, 1),
                    recommended=not blocked,
                    explanation=explanation,
                    key_factors=factors,
                ))
            except Exception as exc:
                logger.warning("PD scoring failed for %s: %s", opt.option.id, exc)
                return self._fallback.score(packet)

        ranked = sorted(scores, key=lambda s: (0 if s.recommended else 1, s.risk_score))
        best = ranked[0].option_id
        return ScoringResult(
            options=scores,
            best_option_id=best,
            summary=(
                f"Mô hình PD gợi ý: {best} "
                f"(rủi ro {ranked[0].risk_score:.1f}/100)"
            ),
            scorer_used="pd_model",
        )
