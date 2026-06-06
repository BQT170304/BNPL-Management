from __future__ import annotations

from pydantic import BaseModel


class CifsOut(BaseModel):
    cifs: list[str]


class CifSeedOut(BaseModel):
    cif: str
    income: int
    expense: int
    debt_payment: int
