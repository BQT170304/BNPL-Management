from __future__ import annotations

import boto3

from app.core.clock import SystemClock
from app.core.config import Settings, get_settings
from app.core.database import build_engine, build_sessionmaker
from app.modules.advisory.application.ports import RiskScorer
from app.modules.advisory.application.services import EvaluatePurchaseService
from app.modules.advisory.domain.scoring import ScoreWeights
from app.modules.analysis.application.services import AnalysisService
from app.modules.analysis.domain.allocation import get_strategy
from app.modules.auth.application.service import AuthService
from app.modules.explanation.infrastructure.bedrock_scorer import BedrockScorer
from app.modules.explanation.infrastructure.deterministic_scorer import DeterministicScorer
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
from app.modules.profiles.application.ports import ProfileRepository
from app.modules.profiles.infrastructure.memory_repository import InMemoryProfileRepository
from app.modules.profiles.infrastructure.sqlalchemy_repository import (
    SqlAlchemyProfileRepository,
)

_settings = get_settings()
if _settings.persistence == "postgres":
    _sessionmaker = build_sessionmaker(build_engine(_settings.database_url))
    _repo: ProfileRepository = SqlAlchemyProfileRepository(_sessionmaker)
else:
    _repo = InMemoryProfileRepository()


def get_repository() -> ProfileRepository:
    return _repo


def _weights(s: Settings) -> ScoreWeights:
    return ScoreWeights(s.score_weight_cashflow, s.score_weight_goal,
                        s.score_weight_efr, s.score_weight_dti)


def get_scorer() -> RiskScorer:
    s = get_settings()
    fallback = DeterministicScorer(_weights(s))
    if not s.bedrock_enabled:
        return fallback
    client = boto3.client("bedrock-runtime", region_name=s.aws_region)
    return BedrockScorer(client=client, model_id=s.bedrock_model_id, fallback=fallback)


def get_analysis_service() -> AnalysisService:
    s = get_settings()
    return AnalysisService(SystemClock(), get_strategy(s.allocation_strategy))


def get_evaluate_service() -> EvaluatePurchaseService:
    return EvaluatePurchaseService(analysis=get_analysis_service(), scorer=get_scorer())


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
