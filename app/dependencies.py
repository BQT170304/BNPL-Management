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
from app.modules.consent.application.ports import CifLinkRepository, ConsentRepository
from app.modules.consent.application.services import ConsentService
from app.modules.consent.infrastructure.memory_repository import (
    InMemoryCifLinkRepository,
    InMemoryConsentRepository,
)
from app.modules.copilot.application.services import CopilotService
from app.modules.decisions.application.ports import DecisionRepository
from app.modules.decisions.application.services import DecisionService
from app.modules.decisions.infrastructure.memory_repository import InMemoryDecisionRepository
from app.modules.explanation.application.explain_service import ExplainService
from app.modules.explanation.infrastructure.bedrock_scorer import BedrockScorer
from app.modules.explanation.infrastructure.hard_rule_scorer import HardRuleScorer
from app.modules.explanation.infrastructure.local_llm_scorer import LocalLLMScorer
from app.modules.explanation.infrastructure.pd_backed_scorer import PDBackedScorer
from app.modules.feedback.application.ports import OutcomeRepository
from app.modules.feedback.application.services import FeedbackService
from app.modules.feedback.infrastructure.memory_repository import InMemoryOutcomeRepository
from app.modules.forecasting.application.cashflow_forecaster import (
    BaseCashflowForecaster,
    FlatCashflowForecaster,
    ProphetCashflowForecaster,
)
from app.modules.forecasting.application.daily_history import DailyCashflowHistoryProvider
from app.modules.forecasting.application.daily_service import DailyForecastService
from app.modules.forecasting.application.history_provider import (
    CashflowHistoryProvider,
    CifCashflowHistoryProvider,
)
from app.modules.forecasting.application.services import ForecastService
from app.modules.ingestion.application.service import IngestionService
from app.modules.ingestion.infrastructure.csv_source import CsvSummarySource
from app.modules.ingestion.infrastructure.transaction_csv_source import CsvTransactionSource
from app.modules.ml.infrastructure.pd_scorer import PDScorer
from app.modules.obligations.application.ports import ObligationRepository
from app.modules.obligations.application.services import ObligationService
from app.modules.obligations.infrastructure.memory_repository import InMemoryObligationRepository
from app.modules.planning.application.optimizer import ConstraintOptimizer
from app.modules.planning.application.simulator import ScenarioSimulator
from app.modules.portfolio.application.services import PortfolioService
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
    PD model → LocalLLM → Bedrock → HardRules
    """
    s = get_settings()
    base: RiskScorer = HardRuleScorer()

    if s.bedrock_enabled:
        client = boto3.client("bedrock-runtime", region_name=s.aws_region)
        base = BedrockScorer(client=client, model_id=s.bedrock_model_id, fallback=base)

    if s.local_llm_enabled:
        base = LocalLLMScorer(
            url=s.local_llm_url, auth=s.local_llm_auth,
            model=s.local_llm_model, fallback=base,
        )

    if s.ml_enabled:
        pd = PDScorer(model_path=s.ml_model_path)
        if pd.is_available():
            base = PDBackedScorer(pd_scorer=pd, fallback=base)

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


_obligation_repo = InMemoryObligationRepository()
_decision_repo = InMemoryDecisionRepository()
_consent_repo = InMemoryConsentRepository()
_cif_link_repo = InMemoryCifLinkRepository()
_outcome_repo = InMemoryOutcomeRepository()


def get_obligation_repository() -> ObligationRepository:
    return _obligation_repo


def get_decision_repository() -> DecisionRepository:
    return _decision_repo


def get_consent_repository() -> ConsentRepository:
    return _consent_repo


def get_cif_link_repository() -> CifLinkRepository:
    return _cif_link_repo


def get_consent_service() -> ConsentService:
    return ConsentService(get_consent_repository(), get_cif_link_repository())


def get_decision_service() -> DecisionService:
    return DecisionService(get_decision_repository())


def get_outcome_repository() -> OutcomeRepository:
    return _outcome_repo


def get_feedback_service() -> FeedbackService:
    return FeedbackService(get_outcome_repository(), get_decision_repository())


def get_obligation_service() -> ObligationService:
    return ObligationService(obligations=get_obligation_repository(), profiles=get_repository())


def _build_forecast_service() -> ForecastService:
    settings = get_settings()
    base_forecaster: BaseCashflowForecaster
    history_provider: CashflowHistoryProvider | None
    if settings.forecast_engine == "prophet":
        base_forecaster = ProphetCashflowForecaster()
        history_provider = CifCashflowHistoryProvider(
            get_cif_link_repository(), get_ingestion_service()
        )
    else:
        base_forecaster = FlatCashflowForecaster()
        history_provider = None
    return ForecastService(
        clock=SystemClock(),
        obligations=get_obligation_repository(),
        low_confidence_threshold=settings.low_confidence_threshold,
        base_forecaster=base_forecaster,
        history_provider=history_provider,
    )


def get_forecast_service() -> ForecastService:
    return _build_forecast_service()


def get_daily_forecast_service() -> DailyForecastService:
    return DailyForecastService(
        DailyCashflowHistoryProvider(get_cif_link_repository(), get_ingestion_service())
    )


def get_scenario_simulator() -> ScenarioSimulator:
    clock = SystemClock()
    settings = get_settings()
    return ScenarioSimulator(
        clock=clock,
        forecast=_build_forecast_service(),
        analysis=AnalysisService(clock, get_strategy(settings.allocation_strategy)),
    )


def get_constraint_optimizer() -> ConstraintOptimizer:
    return ConstraintOptimizer(
        get_scenario_simulator(),
        obligations=get_obligation_repository(),
        low_confidence_threshold=get_settings().low_confidence_threshold,
    )


def get_portfolio_service() -> PortfolioService:
    return PortfolioService(get_ingestion_service())


def get_copilot_service() -> CopilotService:
    return CopilotService(
        profiles=get_repository(),
        optimizer=get_constraint_optimizer(),
        decisions=get_decision_service(),
        forecast=get_forecast_service(),
        analysis=get_analysis_service(),
        obligations=get_obligation_service(),
        efr_safe_months=get_settings().efr_safe_months,
    )


_ingestion_service: IngestionService | None = None


def get_ingestion_service() -> IngestionService:
    global _ingestion_service
    if _ingestion_service is None:
        s = get_settings()
        _ingestion_service = IngestionService(
            CsvSummarySource(),
            s.ingestion_csv_path,
            transaction_source=CsvTransactionSource(),
            transaction_csv_path=s.transaction_csv_path,
        )
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


