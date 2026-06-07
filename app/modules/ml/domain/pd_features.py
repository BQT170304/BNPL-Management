"""Feature vector for the PD (Probability of Default) model.

Five features derived from the Taiwan Credit Card Default dataset
(UCI, 30K real samples). All coefficients are learned from data.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PDFeatureVector:
    util_ratio: float    # debt / capacity ratio (maps to DTI/100)
    max_dpd: float       # worst payment delay in months
    avg_dpd: float       # average payment delay
    pay_coverage: float  # payment made vs. bill amount (clipped 0-3)
    log_limit: float     # log1p(credit_limit proxy)

    FEATURE_NAMES: tuple[str, ...] = (
        "util_ratio", "max_dpd", "avg_dpd", "pay_coverage", "log_limit",
    )

    def to_list(self) -> list[float]:
        return [self.util_ratio, self.max_dpd, self.avg_dpd, self.pay_coverage, self.log_limit]
