from __future__ import annotations

from datetime import UTC, date, datetime

from app.modules.obligations.application.services import ObligationService
from app.modules.obligations.domain.entities import Obligation, ObligationType
from app.modules.obligations.infrastructure.memory_repository import InMemoryObligationRepository
from app.modules.profiles.infrastructure.memory_repository import InMemoryProfileRepository

NOW = datetime(2026, 6, 6, tzinfo=UTC)


def _service(repo: InMemoryObligationRepository) -> ObligationService:
    return ObligationService(repo, InMemoryProfileRepository(), now=lambda: NOW)


def _obligation() -> Obligation:
    return Obligation(
        id="auto_1",
        profile_id="p1",
        type=ObligationType.LOAN,
        merchant="tra gop",
        category="debt",
        principal_amount=6_000_000,
        monthly_payment=500_000,
        due_day=10,
        start_date=date(2026, 1, 1),
        confidence=0.4,
    )


async def test_verify_promotes_confidence_and_records_actor():
    repo = InMemoryObligationRepository()
    await repo.add(_obligation())
    verified = await _service(repo).verify("auto_1", "rm_bob")
    assert verified.confidence == 1.0
    assert verified.verified is True
    assert verified.verified_by == "rm_bob"
    assert verified.verified_at == NOW
    # persisted
    assert (await repo.get("auto_1")).verified_by == "rm_bob"
