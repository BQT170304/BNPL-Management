# app/modules/analysis/domain/thresholds.py
from __future__ import annotations

from enum import Enum


class DtiBand(str, Enum):
    SAFE = "SAFE"             # < 20
    ACCEPTABLE = "ACCEPTABLE" # 20–35
    WARNING = "WARNING"       # 35–40
    DANGER = "DANGER"         # > 40 (and == 40)


def classify_dti(value: float) -> DtiBand:
    if value < 20:
        return DtiBand.SAFE
    if value < 35:
        return DtiBand.ACCEPTABLE
    if value < 40:
        return DtiBand.WARNING
    return DtiBand.DANGER
