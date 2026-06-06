import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL_TEST"), reason="no test database configured"
)


@pytest.fixture
async def repo():
    from app.core.database import Base, build_engine, build_sessionmaker
    from app.modules.profiles.infrastructure.sqlalchemy_repository import (
        SqlAlchemyProfileRepository,
    )
    engine = build_engine(os.environ["DATABASE_URL_TEST"])
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield SqlAlchemyProfileRepository(build_sessionmaker(engine))
    await engine.dispose()


async def test_round_trip(repo):
    from app.modules.profiles.domain.entities import Expense, FinancialProfile, Income
    from app.modules.profiles.domain.value_objects import ExpenseClass, RiskTolerance
    p = FinancialProfile(
        id="p1", income=Income(10_000_000), risk=RiskTolerance.LOW,
        emergency_fund=20_000_000,
        expenses=[Expense("rent", 3_000_000, ExpenseClass.FIXED)],
    )
    await repo.add(p)
    got = await repo.get("p1")
    assert got.total_income == 10_000_000
    assert got.essential_expense == 3_000_000
