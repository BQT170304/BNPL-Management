# app/modules/profiles/domain/value_objects.py
from __future__ import annotations

from enum import Enum


class ExpenseClass(str, Enum):
    FIXED = "FIXED"
    SEMI_FIXED = "SEMI_FIXED"
    DISCRETIONARY = "DISCRETIONARY"


class DebtType(str, Enum):
    REVOLVING = "REVOLVING"
    INSTALLMENT = "INSTALLMENT"
    SECURED = "SECURED"


class AssetType(str, Enum):
    CASH = "CASH"
    SAVINGS = "SAVINGS"
    OTHER = "OTHER"


class Liquidity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RiskTolerance(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
