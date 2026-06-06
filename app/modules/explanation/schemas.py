# app/modules/explanation/schemas.py
from __future__ import annotations

from pydantic import BaseModel, Field


class LLMOptionScore(BaseModel):
    option_id: str
    risk_score: float = Field(ge=0, le=100)
    recommended: bool
    explanation: str
    key_factors: list[str] = Field(default_factory=list)


class LLMScoringResponse(BaseModel):
    options: list[LLMOptionScore]
    best_option_id: str
    summary: str
