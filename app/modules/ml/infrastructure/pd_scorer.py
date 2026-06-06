"""Load a trained PD (Probability of Default) model and score BNPL options.

PD model: Logistic Regression trained on Taiwan Credit Card Default dataset.
Score conversion: industry-standard credit scorecard formula
  Score = Offset − Factor × ln(PD / (1 − PD))
  with Offset=600, Factor=20, clamped to [300, 850].

Risk score (0–100, higher = riskier):
  risk = (850 − score) / 5.5
"""
from __future__ import annotations

import logging
import math
import pickle
from pathlib import Path
from typing import Any

from app.modules.ml.domain.pd_features import PDFeatureVector

logger = logging.getLogger(__name__)

_OFFSET = 600
_FACTOR = 20
_SCORE_MAX = 850
_SCORE_MIN = 300


def pd_to_credit_score(pd_val: float) -> int:
    pd_val = max(1e-6, min(1 - 1e-6, pd_val))
    raw = _OFFSET - _FACTOR * math.log(pd_val / (1 - pd_val))
    return int(max(_SCORE_MIN, min(_SCORE_MAX, round(raw))))


def credit_score_to_risk(score: int) -> float:
    return round((_SCORE_MAX - score) / (_SCORE_MAX - _SCORE_MIN) * 100.0, 1)


class PDScorer:
    def __init__(self, model_path: str = "models/pd_model.pkl") -> None:
        self._path = Path(model_path)
        self._artifact: dict[str, Any] | None = None
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            logger.info("No PD model at %s — PD scoring disabled", self._path)
            return
        try:
            with open(self._path, "rb") as f:
                self._artifact = pickle.load(f)
            logger.info("Loaded PD model from %s", self._path)
        except Exception as exc:
            logger.warning("Failed to load PD model: %s", exc)

    def is_available(self) -> bool:
        return self._artifact is not None

    def predict_pd(self, features: PDFeatureVector) -> float:
        if not self.is_available():
            raise RuntimeError("PD model not loaded")
        import numpy as np
        pipeline = self._artifact["pipeline"]  # type: ignore[index]
        X = np.array([features.to_list()])
        return float(pipeline.predict_proba(X)[0, 1])

    def score_option(self, features: PDFeatureVector) -> tuple[int, float]:
        """Return (credit_score, risk_score_0_to_100)."""
        pd_val = self.predict_pd(features)
        cs = pd_to_credit_score(pd_val)
        risk = credit_score_to_risk(cs)
        return cs, risk
