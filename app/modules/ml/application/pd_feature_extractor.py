"""Maps BNPL scoring context (OptionPacket + ScoringPacket) to PDFeatureVector.

Conceptual mapping to Taiwan dataset features:
  util_ratio    ← dti_new / 100       (debt burden as fraction of income capacity)
  max_dpd       ← 0 if ncf_new >= 0, 2 if ncf_new < 0   (proxy: can't pay = likely to delay)
  avg_dpd       ← -1 if ncf_new >= 0, 0 if ncf_new < 0  (paid-in-full vs. revolving proxy)
  pay_coverage  ← clamped(max(0, ncf_new) / max(1, |payment|), 0, 3)
  log_limit     ← log1p(efr_after * 12)   (emergency buffer as creditworthiness proxy)
"""
from __future__ import annotations

import math

from app.modules.advisory.application.dto import OptionPacket, ScoringPacket
from app.modules.ml.domain.pd_features import PDFeatureVector


class PDFeatureExtractor:
    def extract(self, packet: ScoringPacket, opt: OptionPacket) -> PDFeatureVector:
        util_ratio = max(0.0, opt.dti_new / 100.0)

        if opt.ncf_new >= 0:
            max_dpd = 0.0
            avg_dpd = -1.0
        else:
            max_dpd = 2.0
            avg_dpd = 0.0

        payment = abs(opt.payment) or 1
        pay_coverage = min(3.0, max(0.0, opt.ncf_new) / payment)

        log_limit = math.log1p(max(0.0, opt.efr_after * 12))

        return PDFeatureVector(
            util_ratio=util_ratio,
            max_dpd=max_dpd,
            avg_dpd=avg_dpd,
            pay_coverage=pay_coverage,
            log_limit=log_limit,
        )
