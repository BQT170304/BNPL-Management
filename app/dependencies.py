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
from app.modules.explanation.infrastructure.bedrock_scorer import BedrockScorer
from app.modules.explanation.infrastructure.deterministic_scorer import DeterministicScorer
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
