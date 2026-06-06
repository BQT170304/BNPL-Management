import pytest

from app.core.errors import ProfileNotFound
from app.modules.profiles.domain.entities import FinancialProfile, Income
from app.modules.profiles.domain.value_objects import RiskTolerance
from app.modules.profiles.infrastructure.memory_repository import InMemoryProfileRepository


def _profile(pid: str = "p1") -> FinancialProfile:
    return FinancialProfile(id=pid, income=Income(10_000_000), risk=RiskTolerance.LOW)


async def test_add_and_get():
    repo = InMemoryProfileRepository()
    await repo.add(_profile())
    fetched = await repo.get("p1")
    assert fetched.id == "p1"


async def test_get_missing_raises():
    repo = InMemoryProfileRepository()
    with pytest.raises(ProfileNotFound):
        await repo.get("nope")


async def test_update_replaces():
    repo = InMemoryProfileRepository()
    await repo.add(_profile())
    updated = _profile()
    updated.emergency_fund = 5_000_000
    await repo.update(updated)
    assert (await repo.get("p1")).emergency_fund == 5_000_000
