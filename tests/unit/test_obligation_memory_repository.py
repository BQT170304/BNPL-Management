from __future__ import annotations

from datetime import date

import pytest

from app.core.errors import ObligationNotFound
from app.modules.obligations.domain.entities import Obligation, ObligationType
from app.modules.obligations.infrastructure.memory_repository import InMemoryObligationRepository


def _obligation(oid: str, profile_id: str = "p1", due_day: int = 15) -> Obligation:
    return Obligation(
        id=oid,
        profile_id=profile_id,
        type=ObligationType.BNPL,
        merchant="Store",
        category="electronics",
        principal_amount=12_000_000,
        monthly_payment=2_000_000,
        due_day=due_day,
        start_date=date(2026, 7, 1),
        remaining_terms=6,
    )


async def test_add_and_list_by_profile():
    repo = InMemoryObligationRepository()
    await repo.add(_obligation("obl_2", due_day=20))
    await repo.add(_obligation("obl_1", due_day=10))
    await repo.add(_obligation("other", profile_id="p2"))

    obligations = await repo.list_by_profile("p1")

    assert [o.id for o in obligations] == ["obl_1", "obl_2"]


async def test_delete_removes_obligation():
    repo = InMemoryObligationRepository()
    await repo.add(_obligation("obl_1"))

    await repo.delete("p1", "obl_1")

    assert await repo.list_by_profile("p1") == []


async def test_delete_missing_raises():
    repo = InMemoryObligationRepository()
    with pytest.raises(ObligationNotFound):
        await repo.delete("p1", "missing")


async def test_delete_wrong_profile_raises():
    repo = InMemoryObligationRepository()
    await repo.add(_obligation("obl_1", profile_id="p1"))

    with pytest.raises(ObligationNotFound):
        await repo.delete("p2", "obl_1")
