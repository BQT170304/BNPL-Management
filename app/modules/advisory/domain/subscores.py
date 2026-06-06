# app/modules/advisory/domain/subscores.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SubScores:
    cashflow: int
    goal: float
    efr: int
    dti: int


def s_cashflow(payment: int, ncf: int) -> int:
    """100 if payment<=50% NCF, 60 if 50–80%, 20 if 80–100%, 0 if payment>NCF."""
    if payment <= 0:
        return 100
    if ncf <= 0:
        return 0
    pct = payment / ncf
    if pct <= 0.5:
        return 100
    if pct <= 0.8:
        return 60
    if pct <= 1.0:
        return 20
    return 0


def s_goal(delta_pgrs: float) -> float:
    """100 - min(100, ΔPGRS*3). Continuous form is source of truth."""
    return 100.0 - min(100.0, max(0.0, delta_pgrs) * 3.0)


def s_efr(efr_after: float) -> int:
    """>=6 ->100, 3–6 ->70, 1–3 ->30, <1 ->0."""
    if efr_after >= 6:
        return 100
    if efr_after >= 3:
        return 70
    if efr_after >= 1:
        return 30
    return 0


def s_dti(dti_new: float) -> int:
    """<20 ->100, 20–35 ->70, 35–40 ->40, >40 ->0."""
    if dti_new < 20:
        return 100
    if dti_new < 35:
        return 70
    if dti_new < 40:
        return 40
    return 0
