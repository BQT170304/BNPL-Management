from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    persistence: Literal["memory", "sqlite", "postgres"] = "sqlite"
    sqlite_path: str = "bnpl.db"
    database_url: str = "postgresql+asyncpg://bnpl:bnpl@localhost:5432/bnpl"
    database_url_test: str = "postgresql+asyncpg://bnpl:bnpl@localhost:5432/bnpl_test"

    bedrock_enabled: bool = False
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"

    allocation_strategy: Literal["weighted", "even"] = "weighted"
    efr_safe_months: int = 3

    ingestion_csv_path: str = "data/summary_by_cif_month.csv"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    auth_enabled: bool = True
    auth_username: str = "nguyenvana"
    auth_password: str = "123456"
    auth_token: str = "demo-token-bnpl"        # bearer returned on login
    transactions_csv_path: str = "data/demo_transactions_10001234.csv"
    forecast_horizon_days: int = 90
    forecast_min_active_days: int = 20
    prophet_enabled: bool = True
    demo_cif: str = "10001234"

    # ── Local hosted LLM (OpenAI-compatible) ────────────────────────────────
    local_llm_enabled: bool = False
    local_llm_url: str = "http://203.113.152.4:7777/llm/v1/chat/completions"
    local_llm_auth: str = "Basic dmlldHRlbF9haTpWYWlAMjAyNQ=="
    local_llm_model: str = "Qwen3-14B"

    # ── ML PD (Probability of Default) model — trained on Taiwan Credit Card Default data ──
    ml_model_path: str = "models/pd_model.pkl"
    ml_enabled: bool = True   # auto-detected: only active when model file exists


@lru_cache
def get_settings() -> Settings:
    return Settings()
