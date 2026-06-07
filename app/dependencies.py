from __future__ import annotations

import boto3

from app.core.clock import SystemClock
from app.core.config import get_settings
from app.core.database import build_engine, build_sessionmaker
from app.modules.advisory.application.ports import RiskScorer
from app.modules.advisory.application.services import EvaluatePurchaseService
from app.modules.analysis.application.services import AnalysisService
from app.modules.analysis.domain.allocation import get_strategy
from app.modules.auth.application.service import AuthService
from app.modules.explanation.application.explain_service import ExplainService
from app.modules.explanation.infrastructure.bedrock_scorer import BedrockScorer
from app.modules.explanation.infrastructure.hard_rule_scorer import HardRuleScorer
from app.modules.explanation.infrastructure.local_llm_scorer import LocalLLMScorer
from app.modules.explanation.infrastructure.pd_backed_scorer import PDBackedScorer
from app.modules.forecasting.application.ports import Forecaster
from app.modules.forecasting.application.service import ForecastService
from app.modules.forecasting.infrastructure.csv_transaction_source import (
    CsvTransactionSource,
)
from app.modules.forecasting.infrastructure.matplotlib_chart import MatplotlibChart
from app.modules.forecasting.infrastructure.naive_forecaster import NaiveForecaster
from app.modules.forecasting.infrastructure.prophet_forecaster import ProphetForecaster
from app.modules.ingestion.application.service import IngestionService
from app.modules.ingestion.infrastructure.csv_source import CsvSummarySource
from app.modules.ml.infrastructure.pd_scorer import PDScorer
from app.modules.profiles.application.ports import ProfileRepository
from app.modules.profiles.infrastructure.memory_repository import InMemoryProfileRepository
from app.modules.profiles.infrastructure.sqlalchemy_repository import (
    SqlAlchemyProfileRepository,
)

_settings = get_settings()
_db_engine = None

if _settings.persistence == "postgres":
    _db_engine = build_engine(_settings.database_url)
    _repo: ProfileRepository = SqlAlchemyProfileRepository(build_sessionmaker(_db_engine))
elif _settings.persistence == "sqlite":
    _db_engine = build_engine(f"sqlite+aiosqlite:///{_settings.sqlite_path}")
    _repo: ProfileRepository = SqlAlchemyProfileRepository(build_sessionmaker(_db_engine))
else:
    _repo = InMemoryProfileRepository()


def get_repository() -> ProfileRepository:
    return _repo


def get_db_engine():
    return _db_engine


def get_scorer() -> RiskScorer:
    """Scorer priority (outermost wins, each wraps the next as fallback):
    LocalLLM → PD model → Bedrock → HardRules
    """
    s = get_settings()
    base: RiskScorer = HardRuleScorer()

    if s.bedrock_enabled:
        client = boto3.client("bedrock-runtime", region_name=s.aws_region)
        base = BedrockScorer(client=client, model_id=s.bedrock_model_id, fallback=base)

    if s.ml_enabled:
        pd = PDScorer(model_path=s.ml_model_path)
        if pd.is_available():
            base = PDBackedScorer(pd_scorer=pd, fallback=base)

    if s.local_llm_enabled:
        base = LocalLLMScorer(
            url=s.local_llm_url, auth=s.local_llm_auth,
            model=s.local_llm_model, fallback=base,
        )

    return base


def get_analysis_service() -> AnalysisService:
    s = get_settings()
    return AnalysisService(SystemClock(), get_strategy(s.allocation_strategy))


def get_evaluate_service() -> EvaluatePurchaseService:
    return EvaluatePurchaseService(analysis=get_analysis_service(), scorer=get_scorer())


def get_explain_service() -> ExplainService:
    s = get_settings()
    return ExplainService(
        llm_url=s.local_llm_url,
        llm_auth=s.local_llm_auth,
        llm_model=s.local_llm_model,
        llm_enabled=s.local_llm_enabled,
    )


_ingestion_service: IngestionService | None = None


def get_ingestion_service() -> IngestionService:
    global _ingestion_service
    if _ingestion_service is None:
        s = get_settings()
        _ingestion_service = IngestionService(CsvSummarySource(), s.ingestion_csv_path)
    return _ingestion_service


_auth_service: AuthService | None = None


def get_auth_service() -> AuthService:
    global _auth_service
    if _auth_service is None:
        s = get_settings()
        _auth_service = AuthService(
            s.auth_username, s.auth_password, s.auth_token, s.auth_enabled
        )
    return _auth_service


_forecast_service: ForecastService | None = None


def get_forecast_service() -> ForecastService:
    global _forecast_service
    if _forecast_service is None:
        s = get_settings()
        source = CsvTransactionSource(s.transactions_csv_path)
        renderer = MatplotlibChart()
        forecaster: Forecaster = NaiveForecaster()
        if s.prophet_enabled:
            try:
                import prophet  # noqa: F401  (probe only; ProphetForecaster imports lazily)

                forecaster = ProphetForecaster()
            except ImportError:
                forecaster = NaiveForecaster()
        _forecast_service = ForecastService(
            source, forecaster, renderer, s.forecast_horizon_days
        )
    return _forecast_service
