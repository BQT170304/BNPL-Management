from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    persistence: Literal["memory", "postgres"] = "memory"
    database_url: str = "postgresql+asyncpg://bnpl:bnpl@localhost:5432/bnpl"
    database_url_test: str = "postgresql+asyncpg://bnpl:bnpl@localhost:5432/bnpl_test"

    bedrock_enabled: bool = False
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"

    allocation_strategy: Literal["weighted", "even"] = "weighted"
    efr_safe_months: int = 3

    ingestion_csv_path: str = "summary_by_cif_month.csv"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    score_weight_cashflow: float = 0.35
    score_weight_goal: float = 0.35
    score_weight_efr: float = 0.20
    score_weight_dti: float = 0.10

    auth_enabled: bool = True
    auth_username: str = "nguyenvana"
    auth_password: str = "123456"
    auth_token: str = "demo-token-bnpl"        # bearer returned on login
    transactions_csv_path: str = "transactions_labeled.csv"
    forecast_horizon_days: int = 90
    forecast_min_active_days: int = 20
    prophet_enabled: bool = True
    demo_cif: str = "10000327"


@lru_cache
def get_settings() -> Settings:
    return Settings()
