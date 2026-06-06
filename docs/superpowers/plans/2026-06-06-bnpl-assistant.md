# BNPL Assistant Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the MVP core logic of a personal-finance advisory service that computes financial-health metrics deterministically and uses an LLM (AWS Bedrock) to assign 0–100 risk scores to payment options for a proposed purchase, with a deterministic fallback.

**Architecture:** Clean Architecture in a modular monolith (FastAPI). Layers per module: `domain` (pure) → `application` (use cases + ports) → `infrastructure` (adapters) → `api` (routers/schemas). Dependencies point inward. Persistence is behind a port: in-memory adapter is the default (runs with zero infra); a Postgres/SQLAlchemy adapter implements the same port.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, pydantic-settings, async SQLAlchemy 2.0 + asyncpg (optional adapter), boto3 (Bedrock), pytest + pytest-asyncio, ruff, mypy (strict), uvicorn.

**Reference spec:** `docs/superpowers/specs/2026-06-06-bnpl-assistant-design.md`

**Conventions for every task:** Money is `int` VNĐ. No floats for currency. Domain code imports no framework. Run `ruff check . && mypy app` before each commit. Use Conventional Commits.

---

## File structure (locked decisions)

```
app/
  __init__.py
  main.py
  core/
    __init__.py
    config.py        # Settings (pydantic-settings)
    clock.py         # Clock protocol, SystemClock, FixedClock
    money.py         # Money helpers (int VND)
    errors.py        # domain exceptions + FastAPI handlers
  modules/
    __init__.py
    profiles/
      __init__.py
      domain/__init__.py value_objects.py entities.py
      application/__init__.py ports.py
      infrastructure/__init__.py memory_repository.py
      api/__init__.py schemas.py router.py
    goals/
      __init__.py
      domain/__init__.py entities.py
    analysis/
      __init__.py
      domain/__init__.py formulas.py thresholds.py allocation.py results.py
      application/__init__.py services.py
      api/__init__.py schemas.py router.py
    advisory/
      __init__.py
      domain/__init__.py options.py subscores.py scoring.py
      application/__init__.py dto.py ports.py services.py
      api/__init__.py schemas.py router.py
    explanation/
      __init__.py
      infrastructure/__init__.py deterministic_scorer.py bedrock_scorer.py
    ingestion/
      __init__.py
      application/__init__.py ports.py services.py
      infrastructure/__init__.py csv_source.py
tests/
  __init__.py
  conftest.py
  unit/...
  integration/...
pyproject.toml
.env.example
README.md
```

Persistence note: Tasks 1–17 build and fully test the core logic + API with the in-memory repo. **Task 18 (Postgres/SQLAlchemy adapter) is the approved production persistence**, behind the same `ProfileRepository` port; it is additive and does not change any core code.

---

## Task 1: Project scaffold + tooling

**Files:**
- Create: `pyproject.toml`, `.env.example`, `app/__init__.py`, `app/core/__init__.py`, `app/modules/__init__.py`, `tests/__init__.py`, `tests/conftest.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "bnpl-assistant"
version = "0.1.0"
description = "BNPL Assistant — personal finance advisory MVP"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]>=0.29",
    "pydantic>=2.6",
    "pydantic-settings>=2.2",
    "boto3>=1.34",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.29",
    "alembic>=1.13",
    "pandas>=2.2",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "httpx>=0.27",
    "ruff>=0.4",
    "mypy>=1.10",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.mypy]
python_version = "3.11"
strict = true
plugins = []
warn_unused_ignores = true

[[tool.mypy.overrides]]
module = ["boto3.*", "botocore.*", "pandas.*"]
ignore_missing_imports = true
```

- [ ] **Step 2: Create `.env.example`**

```env
# Persistence: "memory" (default, no infra) or "postgres"
PERSISTENCE=memory
DATABASE_URL=postgresql+asyncpg://bnpl:bnpl@localhost:5432/bnpl
DATABASE_URL_TEST=postgresql+asyncpg://bnpl:bnpl@localhost:5432/bnpl_test

# Bedrock: when disabled, the deterministic scorer is always used
BEDROCK_ENABLED=false
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0

# Engine config
ALLOCATION_STRATEGY=weighted   # "weighted" or "even"
EFR_SAFE_MONTHS=3
SCORE_WEIGHT_CASHFLOW=0.35
SCORE_WEIGHT_GOAL=0.35
SCORE_WEIGHT_EFR=0.20
SCORE_WEIGHT_DTI=0.10
```

- [ ] **Step 3: Create empty package files**

Create `app/__init__.py`, `app/core/__init__.py`, `app/modules/__init__.py`, `tests/__init__.py` (all empty), and `tests/conftest.py`:

```python
# tests/conftest.py
import pytest
```

- [ ] **Step 4: Install and verify**

Run: `pip install -e ".[dev]"`
Expected: installs without error.
Run: `ruff check . && pytest -q`
Expected: ruff passes; pytest collects 0 tests (exit 0 or "no tests ran").

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .env.example app tests
git commit -m "chore: scaffold project and tooling"
```

---

## Task 2: Money helpers

**Files:**
- Create: `app/core/money.py`
- Test: `tests/unit/test_money.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_money.py
import pytest
from app.core.money import percent, ratio, format_vnd, share_split


def test_percent_basic():
    assert percent(5_500_000, 14_500_000) == pytest.approx(37.93, abs=0.01)


def test_percent_zero_denominator_returns_inf():
    assert percent(1, 0) == float("inf")


def test_percent_zero_over_zero_is_zero():
    assert percent(0, 0) == 0.0


def test_ratio_basic():
    assert ratio(20_000_000, 7_800_000) == pytest.approx(2.564, abs=0.001)


def test_format_vnd():
    assert format_vnd(14_500_000) == "14.500.000 ₫"


def test_share_split_even():
    # split 1_200_000 into 3 equal integer shares, remainder to first
    assert share_split(1_200_000, [1, 1, 1]) == [400_000, 400_000, 400_000]


def test_share_split_weighted_conserves_total():
    parts = share_split(1_000_000, [4, 3, 2])
    assert sum(parts) == 1_000_000
    assert parts[0] > parts[1] > parts[2]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_money.py -v`
Expected: FAIL — `ModuleNotFoundError: app.core.money`.

- [ ] **Step 3: Write minimal implementation**

```python
# app/core/money.py
"""Money helpers. Currency is always int VNĐ; never use float for money."""
from __future__ import annotations

Money = int


def percent(numerator: float, denominator: float) -> float:
    """numerator / denominator as a percentage. 0/0 -> 0; x/0 (x!=0) -> inf."""
    if denominator == 0:
        return 0.0 if numerator == 0 else float("inf")
    return numerator / denominator * 100.0


def ratio(numerator: float, denominator: float) -> float:
    """numerator / denominator as a plain ratio. 0/0 -> 0; x/0 -> inf."""
    if denominator == 0:
        return 0.0 if numerator == 0 else float("inf")
    return numerator / denominator


def format_vnd(amount: Money) -> str:
    """Format an int VNĐ with dot thousands separators, e.g. '14.500.000 ₫'."""
    return f"{amount:,.0f}".replace(",", ".") + " ₫"


def share_split(total: Money, weights: list[int]) -> list[Money]:
    """Split an integer total into shares proportional to weights.

    Uses largest-remainder so the shares sum exactly to total. Empty weights -> [].
    """
    if not weights:
        return []
    weight_sum = sum(weights)
    if weight_sum == 0:
        return [0 for _ in weights]
    raw = [total * w / weight_sum for w in weights]
    floored = [int(x) for x in raw]
    remainder = total - sum(floored)
    # distribute the leftover units to the largest fractional remainders
    order = sorted(range(len(weights)), key=lambda i: raw[i] - floored[i], reverse=True)
    for i in range(remainder):
        floored[order[i % len(order)]] += 1
    return floored
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_money.py -v`
Expected: PASS (6 tests). Create `tests/unit/__init__.py` (empty) if collection complains.

- [ ] **Step 5: Commit**

```bash
git add app/core/money.py tests/unit/test_money.py tests/unit/__init__.py
git commit -m "feat(core): add money helpers (percent, ratio, format, share_split)"
```

---

## Task 3: Clock port

**Files:**
- Create: `app/core/clock.py`
- Test: `tests/unit/test_clock.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_clock.py
from datetime import date
from app.core.clock import FixedClock, SystemClock


def test_fixed_clock_returns_set_date():
    clock = FixedClock(date(2025, 6, 1))
    assert clock.today() == date(2025, 6, 1)


def test_system_clock_returns_a_date():
    assert isinstance(SystemClock().today(), date)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_clock.py -v`
Expected: FAIL — `ModuleNotFoundError: app.core.clock`.

- [ ] **Step 3: Write minimal implementation**

```python
# app/core/clock.py
from __future__ import annotations

from datetime import date
from typing import Protocol


class Clock(Protocol):
    def today(self) -> date: ...


class SystemClock:
    def today(self) -> date:
        return date.today()


class FixedClock:
    def __init__(self, value: date) -> None:
        self._value = value

    def today(self) -> date:
        return self._value
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_clock.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add app/core/clock.py tests/unit/test_clock.py
git commit -m "feat(core): add Clock port with System and Fixed implementations"
```

---

## Task 4: Profiles & Goals domain entities

**Files:**
- Create: `app/modules/profiles/__init__.py`, `app/modules/profiles/domain/__init__.py`, `app/modules/profiles/domain/value_objects.py`, `app/modules/profiles/domain/entities.py`
- Create: `app/modules/goals/__init__.py`, `app/modules/goals/domain/__init__.py`, `app/modules/goals/domain/entities.py`
- Test: `tests/unit/test_profile_domain.py`, `tests/unit/test_goal_domain.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_goal_domain.py
from datetime import date
import pytest
from app.modules.goals.domain.entities import Goal, Priority


def test_priority_weight():
    assert Priority.VERY_HIGH.weight == 4
    assert Priority.LOW.weight == 1


def test_months_remaining_counts_full_months():
    goal = Goal(id="g1", name="Car", target_amount=300_000_000,
                deadline=date(2027, 12, 1), priority=Priority.HIGH)
    assert goal.months_remaining(date(2025, 6, 1)) == 30


def test_months_remaining_floors_at_zero_when_overdue():
    goal = Goal(id="g1", name="Car", target_amount=1,
                deadline=date(2025, 1, 1), priority=Priority.LOW)
    assert goal.months_remaining(date(2025, 6, 1)) == 0


def test_negative_target_rejected():
    with pytest.raises(ValueError):
        Goal(id="g", name="x", target_amount=-1,
             deadline=date(2030, 1, 1), priority=Priority.LOW)
```

```python
# tests/unit/test_profile_domain.py
import pytest
from app.modules.profiles.domain.value_objects import (
    AssetType, DebtType, ExpenseClass, Liquidity, RiskTolerance,
)
from app.modules.profiles.domain.entities import (
    Asset, Debt, Expense, FinancialProfile, Income,
)


def _profile() -> FinancialProfile:
    return FinancialProfile(
        id="p1",
        income=Income(salary=10_000_000, secondary=3_000_000,
                      avg_bonus_monthly=1_000_000, passive=500_000),
        expenses=[
            Expense("rent", 3_000_000, ExpenseClass.FIXED),
            Expense("food", 3_000_000, ExpenseClass.SEMI_FIXED),
            Expense("transport", 500_000, ExpenseClass.SEMI_FIXED),
            Expense("internet", 300_000, ExpenseClass.FIXED),
            Expense("entertainment", 1_000_000, ExpenseClass.DISCRETIONARY),
        ],
        debts=[
            Debt("credit card", 2_000_000, None, 30.0, None, DebtType.REVOLVING),
            Debt("bnpl laptop", 1_500_000, 9_000_000, 0.0, 6, DebtType.INSTALLMENT),
            Debt("car loan", 2_000_000, 100_000_000, 10.0, 50, DebtType.SECURED),
        ],
        assets=[
            Asset(AssetType.CASH, 20_000_000, Liquidity.HIGH),
            Asset(AssetType.SAVINGS, 80_000_000, Liquidity.MEDIUM),
        ],
        emergency_fund=20_000_000,
        risk=RiskTolerance.MEDIUM,
    )


def test_total_income():
    assert _profile().total_income == 14_500_000


def test_total_expense():
    assert _profile().total_expense == 7_800_000


def test_essential_expense_excludes_discretionary():
    # 3,000,000 + 3,000,000 + 500,000 + 300,000 (no entertainment)
    assert _profile().essential_expense == 6_800_000


def test_total_debt_payment():
    assert _profile().total_debt_payment == 5_500_000


def test_negative_salary_rejected():
    with pytest.raises(ValueError):
        Income(salary=-1)
```

> Note: the spec's EFR example divides by 7,800,000 (it labels that "essential"),
> but the EFR formula explicitly excludes discretionary. We follow the **formula**:
> `essential_expense = FIXED + SEMI_FIXED = 6,800,000`. EFR golden numbers in
> Task 6 use 6,800,000.

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_goal_domain.py tests/unit/test_profile_domain.py -v`
Expected: FAIL — modules not found.

- [ ] **Step 3: Write the implementations**

```python
# app/modules/goals/domain/entities.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import IntEnum


class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    VERY_HIGH = 4

    @property
    def weight(self) -> int:
        return int(self.value)


@dataclass
class Goal:
    id: str
    name: str
    target_amount: int
    deadline: date
    priority: Priority
    savings_allocated: int = 0

    def __post_init__(self) -> None:
        if self.target_amount < 0:
            raise ValueError("target_amount must be >= 0")
        if self.savings_allocated < 0:
            raise ValueError("savings_allocated must be >= 0")

    def months_remaining(self, today: date) -> int:
        months = (self.deadline.year - today.year) * 12 + (self.deadline.month - today.month)
        return max(0, months)
```

```python
# app/modules/profiles/domain/value_objects.py
from __future__ import annotations

from enum import Enum


class ExpenseClass(str, Enum):
    FIXED = "FIXED"
    SEMI_FIXED = "SEMI_FIXED"
    DISCRETIONARY = "DISCRETIONARY"


class DebtType(str, Enum):
    REVOLVING = "REVOLVING"
    INSTALLMENT = "INSTALLMENT"
    SECURED = "SECURED"


class AssetType(str, Enum):
    CASH = "CASH"
    SAVINGS = "SAVINGS"
    OTHER = "OTHER"


class Liquidity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RiskTolerance(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
```

```python
# app/modules/profiles/domain/entities.py
from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.goals.domain.entities import Goal
from app.modules.profiles.domain.value_objects import (
    AssetType, DebtType, ExpenseClass, Liquidity, RiskTolerance,
)


@dataclass
class Income:
    salary: int
    secondary: int = 0
    avg_bonus_monthly: int = 0
    passive: int = 0

    def __post_init__(self) -> None:
        for name in ("salary", "secondary", "avg_bonus_monthly", "passive"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be >= 0")

    @property
    def total(self) -> int:
        return self.salary + self.secondary + self.avg_bonus_monthly + self.passive


@dataclass
class Expense:
    category: str
    amount: int
    classification: ExpenseClass

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("expense amount must be >= 0")


@dataclass
class Debt:
    name: str
    monthly_payment: int
    balance: int | None
    apr: float
    months_remaining: int | None
    debt_type: DebtType

    def __post_init__(self) -> None:
        if self.monthly_payment < 0:
            raise ValueError("monthly_payment must be >= 0")


@dataclass
class Asset:
    type: AssetType
    value: int
    liquidity: Liquidity

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("asset value must be >= 0")


@dataclass
class FinancialProfile:
    id: str
    income: Income
    risk: RiskTolerance
    emergency_fund: int = 0
    expenses: list[Expense] = field(default_factory=list)
    debts: list[Debt] = field(default_factory=list)
    assets: list[Asset] = field(default_factory=list)
    goals: list[Goal] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.emergency_fund < 0:
            raise ValueError("emergency_fund must be >= 0")

    @property
    def total_income(self) -> int:
        return self.income.total

    @property
    def total_expense(self) -> int:
        return sum(e.amount for e in self.expenses)

    @property
    def essential_expense(self) -> int:
        return sum(
            e.amount for e in self.expenses
            if e.classification in (ExpenseClass.FIXED, ExpenseClass.SEMI_FIXED)
        )

    @property
    def total_debt_payment(self) -> int:
        return sum(d.monthly_payment for d in self.debts)
```

Create the empty `__init__.py` files listed in this task's Files section.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_goal_domain.py tests/unit/test_profile_domain.py -v`
Expected: PASS (9 tests).

- [ ] **Step 5: Commit**

```bash
git add app/modules/profiles app/modules/goals tests/unit/test_profile_domain.py tests/unit/test_goal_domain.py
git commit -m "feat(domain): add profile and goal entities with computed totals"
```

---

## Task 5: Analysis formulas (the engine core)

**Files:**
- Create: `app/modules/analysis/__init__.py`, `app/modules/analysis/domain/__init__.py`, `app/modules/analysis/domain/formulas.py`
- Test: `tests/unit/test_formulas.py`

- [ ] **Step 1: Write the failing tests (golden numbers from the spec)**

```python
# tests/unit/test_formulas.py
import pytest
from app.modules.analysis.domain import formulas as f


def test_net_cash_flow():
    assert f.net_cash_flow(14_500_000, 7_800_000, 5_500_000) == 1_200_000


def test_dti():
    assert f.dti(5_500_000, 14_500_000) == pytest.approx(37.93, abs=0.01)


def test_saving_rate():
    ncf = 1_200_000
    assert f.saving_rate(ncf, 0, 14_500_000) == pytest.approx(8.28, abs=0.01)


def test_efr():
    assert f.efr(20_000_000, 6_800_000) == pytest.approx(2.94, abs=0.01)


def test_goal_gap():
    assert f.goal_gap(300_000_000, 0) == 300_000_000


def test_gat():
    assert f.gat(300_000_000, 400_000) == pytest.approx(750.0, abs=0.1)


def test_gat_zero_allocation_is_inf():
    assert f.gat(300_000_000, 0) == float("inf")


def test_goal_delay():
    assert f.goal_delay(750.0, 30) == 720.0


def test_grs_caps_at_100():
    assert f.grs(720.0, 30) == 100.0


def test_grs_zero_when_on_time_or_early():
    assert f.grs(-5.0, 30) == 0.0
    assert f.grs(0.0, 30) == 0.0


def test_grs_overdue_months_remaining_zero_is_100():
    assert f.grs(0.0, 0) == 100.0


def test_pgrs_weighted_average():
    # car GRS100 w3, house GRS100 w4, japan GRS100 w2 -> 100
    assert f.pgrs([(100.0, 3), (100.0, 4), (100.0, 2)]) == pytest.approx(100.0)


def test_pgrs_mixed():
    # (0*3 + 50*1) / 4 = 12.5
    assert f.pgrs([(0.0, 3), (50.0, 1)]) == pytest.approx(12.5)


def test_pgrs_no_goals_is_zero():
    assert f.pgrs([]) == 0.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_formulas.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the implementation**

```python
# app/modules/analysis/domain/formulas.py
"""Pure financial formulas. No I/O, no clock, no DB. All amounts are int VNĐ."""
from __future__ import annotations

from app.core.money import percent, ratio


def net_cash_flow(income: int, expense: int, debt_payment: int) -> int:
    """NCF = income - expense - debt payment."""
    return income - expense - debt_payment


def dti(debt_payment: int, income: int) -> float:
    """Debt-to-income ratio as a percentage."""
    return percent(debt_payment, income)


def saving_rate(ncf: int, new_purchase_payment: int, income: int) -> float:
    """(NCF - new purchase payment) / income, as a percentage."""
    return percent(ncf - new_purchase_payment, income)


def efr(emergency_fund: int, essential_expense: int) -> float:
    """Emergency-fund ratio in months of essential expense."""
    return ratio(emergency_fund, essential_expense)


def goal_gap(target: int, savings_allocated: int) -> int:
    """Remaining amount to reach a goal."""
    return max(0, target - savings_allocated)


def gat(gap: int, monthly_saving_allocated: int) -> float:
    """Goal achievement time in months. Zero/negative allocation -> inf."""
    if monthly_saving_allocated <= 0:
        return float("inf") if gap > 0 else 0.0
    return gap / monthly_saving_allocated


def goal_delay(gat_value: float, months_remaining: int) -> float:
    """Months late vs. the deadline. Positive = late."""
    return gat_value - months_remaining


def grs(delay: float, months_remaining: int) -> float:
    """Goal risk score 0..100. Overdue (months_remaining<=0) -> 100."""
    if months_remaining <= 0:
        return 100.0
    return min(100.0, max(0.0, delay / months_remaining * 100.0))


def pgrs(grs_weighted: list[tuple[float, int]]) -> float:
    """Portfolio goal risk: weighted average of per-goal GRS. No goals -> 0."""
    weight_sum = sum(w for _, w in grs_weighted)
    if weight_sum == 0:
        return 0.0
    return sum(score * w for score, w in grs_weighted) / weight_sum
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_formulas.py -v`
Expected: PASS (14 tests).

- [ ] **Step 5: Commit**

```bash
git add app/modules/analysis tests/unit/test_formulas.py
git commit -m "feat(analysis): add pure financial formula functions"
```

---

## Task 6: DTI thresholds

**Files:**
- Create: `app/modules/analysis/domain/thresholds.py`
- Test: `tests/unit/test_thresholds.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_thresholds.py
from app.modules.analysis.domain.thresholds import DtiBand, classify_dti


def test_dti_bands():
    assert classify_dti(15) == DtiBand.SAFE
    assert classify_dti(25) == DtiBand.ACCEPTABLE
    assert classify_dti(37.93) == DtiBand.WARNING
    assert classify_dti(45) == DtiBand.DANGER


def test_dti_band_boundaries_lower_inclusive():
    assert classify_dti(20) == DtiBand.ACCEPTABLE
    assert classify_dti(35) == DtiBand.WARNING
    assert classify_dti(40) == DtiBand.DANGER
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_thresholds.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the implementation**

```python
# app/modules/analysis/domain/thresholds.py
from __future__ import annotations

from enum import Enum


class DtiBand(str, Enum):
    SAFE = "SAFE"             # < 20
    ACCEPTABLE = "ACCEPTABLE" # 20–35
    WARNING = "WARNING"       # 35–40
    DANGER = "DANGER"         # > 40 (and == 40)


def classify_dti(value: float) -> DtiBand:
    if value < 20:
        return DtiBand.SAFE
    if value < 35:
        return DtiBand.ACCEPTABLE
    if value < 40:
        return DtiBand.WARNING
    return DtiBand.DANGER
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_thresholds.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add app/modules/analysis/domain/thresholds.py tests/unit/test_thresholds.py
git commit -m "feat(analysis): add DTI band classification"
```

---

## Task 7: NCF allocation strategies

**Files:**
- Create: `app/modules/analysis/domain/allocation.py`
- Test: `tests/unit/test_allocation.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_allocation.py
from datetime import date
from app.modules.analysis.domain.allocation import EvenAllocation, PriorityWeightedAllocation
from app.modules.goals.domain.entities import Goal, Priority


def _goals():
    return [
        Goal("car", "Car", 300_000_000, date(2027, 12, 1), Priority.HIGH),
        Goal("house", "House", 1_000_000_000, date(2034, 12, 1), Priority.VERY_HIGH),
        Goal("japan", "Japan", 50_000_000, date(2026, 12, 1), Priority.MEDIUM),
    ]


def test_even_allocation_splits_equally():
    alloc = EvenAllocation().allocate(1_200_000, _goals())
    assert alloc == {"car": 400_000, "house": 400_000, "japan": 400_000}


def test_even_allocation_negative_ncf_is_zero():
    alloc = EvenAllocation().allocate(-800_000, _goals())
    assert alloc == {"car": 0, "house": 0, "japan": 0}


def test_weighted_allocation_by_priority_weight():
    # weights 3,4,2 over 900_000 -> 300k,400k,200k
    alloc = PriorityWeightedAllocation().allocate(900_000, _goals())
    assert alloc == {"car": 300_000, "house": 400_000, "japan": 200_000}


def test_allocation_no_goals_returns_empty():
    assert EvenAllocation().allocate(1_000_000, []) == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_allocation.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the implementation**

```python
# app/modules/analysis/domain/allocation.py
from __future__ import annotations

from typing import Protocol

from app.core.money import share_split
from app.modules.goals.domain.entities import Goal


class AllocationStrategy(Protocol):
    def allocate(self, ncf: int, goals: list[Goal]) -> dict[str, int]:
        """Map goal.id -> monthly amount allocated from NCF. Negative NCF -> all 0."""
        ...


class EvenAllocation:
    def allocate(self, ncf: int, goals: list[Goal]) -> dict[str, int]:
        if not goals:
            return {}
        budget = max(0, ncf)
        shares = share_split(budget, [1 for _ in goals])
        return {g.id: s for g, s in zip(goals, shares, strict=True)}


class PriorityWeightedAllocation:
    def allocate(self, ncf: int, goals: list[Goal]) -> dict[str, int]:
        if not goals:
            return {}
        budget = max(0, ncf)
        shares = share_split(budget, [g.priority.weight for g in goals])
        return {g.id: s for g, s in zip(goals, shares, strict=True)}


def get_strategy(name: str) -> AllocationStrategy:
    return EvenAllocation() if name.lower() == "even" else PriorityWeightedAllocation()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_allocation.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add app/modules/analysis/domain/allocation.py tests/unit/test_allocation.py
git commit -m "feat(analysis): add even and priority-weighted NCF allocation"
```

---

## Task 8: Analysis results + service

**Files:**
- Create: `app/modules/analysis/domain/results.py`
- Create: `app/modules/analysis/application/__init__.py`, `app/modules/analysis/application/services.py`
- Test: `tests/unit/test_analysis_service.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_analysis_service.py
from datetime import date
import pytest

from app.core.clock import FixedClock
from app.modules.analysis.application.services import AnalysisService
from app.modules.analysis.domain.allocation import EvenAllocation
from app.modules.analysis.domain.thresholds import DtiBand
from app.modules.goals.domain.entities import Goal, Priority
from app.modules.profiles.domain.entities import (
    Debt, Expense, FinancialProfile, Income,
)
from app.modules.profiles.domain.value_objects import (
    DebtType, ExpenseClass, RiskTolerance,
)


def _profile() -> FinancialProfile:
    return FinancialProfile(
        id="p1",
        income=Income(10_000_000, 3_000_000, 1_000_000, 500_000),
        risk=RiskTolerance.MEDIUM,
        emergency_fund=20_000_000,
        expenses=[
            Expense("rent", 3_000_000, ExpenseClass.FIXED),
            Expense("food", 3_000_000, ExpenseClass.SEMI_FIXED),
            Expense("transport", 500_000, ExpenseClass.SEMI_FIXED),
            Expense("internet", 300_000, ExpenseClass.FIXED),
            Expense("fun", 1_000_000, ExpenseClass.DISCRETIONARY),
        ],
        debts=[
            Debt("cc", 2_000_000, None, 30.0, None, DebtType.REVOLVING),
            Debt("bnpl", 1_500_000, 9_000_000, 0.0, 6, DebtType.INSTALLMENT),
            Debt("car", 2_000_000, 100_000_000, 10.0, 50, DebtType.SECURED),
        ],
        goals=[
            Goal("car", "Car", 300_000_000, date(2027, 12, 1), Priority.HIGH),
            Goal("house", "House", 1_000_000_000, date(2034, 12, 1), Priority.VERY_HIGH),
            Goal("japan", "Japan", 50_000_000, date(2026, 12, 1), Priority.MEDIUM),
        ],
    )


def test_analyze_matches_spec_golden_numbers():
    svc = AnalysisService(clock=FixedClock(date(2025, 6, 1)), allocation=EvenAllocation())
    m = svc.analyze(_profile())

    assert m.ncf == 1_200_000
    assert m.dti == pytest.approx(37.93, abs=0.01)
    assert m.dti_band == DtiBand.WARNING
    assert m.efr == pytest.approx(2.94, abs=0.01)        # 20,000,000 / 6,800,000
    assert m.saving_rate == pytest.approx(8.28, abs=0.01)
    # NCF too low to reach any goal on time -> all GRS 100 -> PGRS 100
    assert m.pgrs == pytest.approx(100.0)
    assert {g.goal_id for g in m.goals} == {"car", "house", "japan"}


def test_analyze_with_extra_payment_lowers_ncf_and_saving_rate():
    svc = AnalysisService(clock=FixedClock(date(2025, 6, 1)), allocation=EvenAllocation())
    m = svc.analyze(_profile(), new_payment=2_000_000)
    # NCF for allocation reflects the new payment: 1,200,000 - 2,000,000 = -800,000
    assert m.ncf == -800_000
    assert m.saving_rate == pytest.approx(percent_neg := (-800_000) / 14_500_000 * 100, abs=0.01)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_analysis_service.py -v`
Expected: FAIL — modules not found.

- [ ] **Step 3: Write the implementations**

```python
# app/modules/analysis/domain/results.py
from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.analysis.domain.thresholds import DtiBand


@dataclass
class GoalMetric:
    goal_id: str
    name: str
    gap: int
    monthly_allocated: int
    gat: float
    delay: float
    grs: float
    months_remaining: int


@dataclass
class ProfileMetrics:
    ncf: int
    dti: float
    dti_band: DtiBand
    saving_rate: float
    efr: float
    pgrs: float
    goals: list[GoalMetric] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
```

```python
# app/modules/analysis/application/services.py
from __future__ import annotations

from app.core.clock import Clock
from app.modules.analysis.domain import formulas as f
from app.modules.analysis.domain.allocation import AllocationStrategy
from app.modules.analysis.domain.results import GoalMetric, ProfileMetrics
from app.modules.analysis.domain.thresholds import classify_dti
from app.modules.profiles.domain.entities import FinancialProfile


class AnalysisService:
    """Assembles deterministic ProfileMetrics from a profile at a point in time."""

    def __init__(self, clock: Clock, allocation: AllocationStrategy) -> None:
        self._clock = clock
        self._allocation = allocation

    def analyze(self, profile: FinancialProfile, new_payment: int = 0) -> ProfileMetrics:
        today = self._clock.today()
        income = profile.total_income
        base_ncf = f.net_cash_flow(income, profile.total_expense, profile.total_debt_payment)
        ncf = base_ncf - new_payment

        dti_value = f.dti(profile.total_debt_payment + new_payment, income)
        saving = f.saving_rate(base_ncf, new_payment, income)
        efr_value = f.efr(profile.emergency_fund, profile.essential_expense)

        allocation = self._allocation.allocate(ncf, profile.goals)
        goal_metrics: list[GoalMetric] = []
        weighted: list[tuple[float, int]] = []
        flags: list[str] = []
        if ncf < 0:
            flags.append("NEGATIVE_CASHFLOW")

        for goal in profile.goals:
            months = goal.months_remaining(today)
            monthly = allocation.get(goal.id, 0)
            gap = f.goal_gap(goal.target_amount, goal.savings_allocated)
            if ncf < 0:
                grs_value, gat_value, delay = 100.0, float("inf"), float("inf")
            else:
                gat_value = f.gat(gap, monthly)
                delay = f.goal_delay(gat_value, months)
                grs_value = f.grs(delay, months)
            goal_metrics.append(GoalMetric(
                goal_id=goal.id, name=goal.name, gap=gap, monthly_allocated=monthly,
                gat=gat_value, delay=delay, grs=grs_value, months_remaining=months,
            ))
            weighted.append((grs_value, goal.priority.weight))

        return ProfileMetrics(
            ncf=ncf,
            dti=dti_value,
            dti_band=classify_dti(dti_value),
            saving_rate=saving,
            efr=efr_value,
            pgrs=f.pgrs(weighted),
            goals=goal_metrics,
            flags=flags,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_analysis_service.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add app/modules/analysis/domain/results.py app/modules/analysis/application tests/unit/test_analysis_service.py
git commit -m "feat(analysis): add ProfileMetrics and AnalysisService"
```

---

## Task 9: Payment options generation

**Files:**
- Create: `app/modules/advisory/__init__.py`, `app/modules/advisory/domain/__init__.py`, `app/modules/advisory/domain/options.py`
- Test: `tests/unit/test_options.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_options.py
from app.modules.advisory.domain.options import (
    PaymentOption, PlanSpec, PlanType, generate_options, default_plans,
)


def test_pay_in_full_option():
    opts = generate_options(15_000_000, [PlanSpec(PlanType.PAY_IN_FULL)])
    assert opts[0].type == PlanType.PAY_IN_FULL
    assert opts[0].monthly_payment == 0
    assert opts[0].upfront == 15_000_000


def test_installment_simple_division():
    opts = generate_options(15_000_000, [PlanSpec(PlanType.INSTALLMENT, months=12)])
    assert opts[0].months == 12
    assert opts[0].monthly_payment == 1_250_000
    assert opts[0].upfront == 0


def test_installment_rounds_up():
    opts = generate_options(10_000_000, [PlanSpec(PlanType.INSTALLMENT, months=3)])
    assert opts[0].monthly_payment == 3_333_334  # ceil(10,000,000/3)


def test_installment_with_apr_is_larger():
    plain = generate_options(12_000_000, [PlanSpec(PlanType.INSTALLMENT, months=12)])[0]
    financed = generate_options(
        12_000_000, [PlanSpec(PlanType.INSTALLMENT, months=12, apr=12.0)]
    )[0]
    assert financed.monthly_payment > plain.monthly_payment


def test_default_plans_are_full_3_6_12():
    opts = generate_options(15_000_000, default_plans())
    labels = [(o.type, o.months) for o in opts]
    assert labels == [
        (PlanType.PAY_IN_FULL, None),
        (PlanType.INSTALLMENT, 3),
        (PlanType.INSTALLMENT, 6),
        (PlanType.INSTALLMENT, 12),
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_options.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the implementation**

```python
# app/modules/advisory/domain/options.py
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum


class PlanType(str, Enum):
    PAY_IN_FULL = "PAY_IN_FULL"
    INSTALLMENT = "INSTALLMENT"


@dataclass(frozen=True)
class PlanSpec:
    type: PlanType
    months: int | None = None
    apr: float = 0.0


@dataclass
class PaymentOption:
    id: str
    label: str
    type: PlanType
    months: int | None
    monthly_payment: int
    upfront: int


def default_plans() -> list[PlanSpec]:
    return [
        PlanSpec(PlanType.PAY_IN_FULL),
        PlanSpec(PlanType.INSTALLMENT, months=3),
        PlanSpec(PlanType.INSTALLMENT, months=6),
        PlanSpec(PlanType.INSTALLMENT, months=12),
    ]


def _amortized_monthly(principal: int, months: int, apr: float) -> int:
    if apr <= 0:
        return math.ceil(principal / months)
    r = apr / 100.0 / 12.0
    payment = principal * r / (1 - (1 + r) ** -months)
    return math.ceil(payment)


def generate_options(amount: int, plans: list[PlanSpec]) -> list[PaymentOption]:
    options: list[PaymentOption] = []
    for spec in plans:
        if spec.type == PlanType.PAY_IN_FULL:
            options.append(PaymentOption(
                id="full", label="Trả thẳng 1 lần", type=spec.type,
                months=None, monthly_payment=0, upfront=amount,
            ))
        else:
            months = spec.months or 0
            if months <= 0:
                raise ValueError("installment plan requires months > 0")
            monthly = _amortized_monthly(amount, months, spec.apr)
            options.append(PaymentOption(
                id=f"installment_{months}", label=f"Trả góp {months} tháng",
                type=spec.type, months=months, monthly_payment=monthly, upfront=0,
            ))
    return options
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_options.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add app/modules/advisory/domain/options.py tests/unit/test_options.py
git commit -m "feat(advisory): add payment option generation"
```

---

## Task 10: Sub-scores + weighted score

**Files:**
- Create: `app/modules/advisory/domain/subscores.py`, `app/modules/advisory/domain/scoring.py`
- Test: `tests/unit/test_subscores.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_subscores.py
import pytest
from app.modules.advisory.domain.subscores import (
    SubScores, s_cashflow, s_dti, s_efr, s_goal,
)
from app.modules.advisory.domain.scoring import ScoreWeights, weighted_option_score


def test_s_cashflow_bands():
    assert s_cashflow(400_000, 1_000_000) == 100   # 40% -> <=50%
    assert s_cashflow(700_000, 1_000_000) == 60    # 70% -> 50–80%
    assert s_cashflow(900_000, 1_000_000) == 20    # 90% -> 80–100%
    assert s_cashflow(1_100_000, 1_000_000) == 0   # > NCF


def test_s_cashflow_pay_in_full_zero_payment_is_safe():
    assert s_cashflow(0, 1_000_000) == 100


def test_s_cashflow_nonpositive_ncf_is_zero_when_payment_positive():
    assert s_cashflow(100_000, 0) == 0
    assert s_cashflow(0, 0) == 100  # nothing paid monthly


def test_s_goal_continuous():
    assert s_goal(0.0) == 100.0
    assert s_goal(10.0) == 70.0
    assert s_goal(20.0) == 40.0
    assert s_goal(40.0) == 0.0   # min cap


def test_s_efr_bands():
    assert s_efr(6.5) == 100
    assert s_efr(4.0) == 70
    assert s_efr(2.0) == 30
    assert s_efr(0.5) == 0


def test_s_dti_bands():
    assert s_dti(15) == 100
    assert s_dti(30) == 70
    assert s_dti(37) == 40
    assert s_dti(45) == 0


def test_weighted_option_score_default_weights():
    sub = SubScores(cashflow=20, goal=70.0, efr=70, dti=40)
    # .35*20 + .35*70 + .20*70 + .10*40 = 7 + 24.5 + 14 + 4 = 49.5
    assert weighted_option_score(sub, ScoreWeights()) == pytest.approx(49.5)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_subscores.py -v`
Expected: FAIL — modules not found.

- [ ] **Step 3: Write the implementations**

```python
# app/modules/advisory/domain/subscores.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SubScores:
    cashflow: int
    goal: float
    efr: int
    dti: int


def s_cashflow(payment: int, ncf: int) -> int:
    """100 if payment<=50% NCF, 60 if 50–80%, 20 if 80–100%, 0 if payment>NCF."""
    if payment <= 0:
        return 100
    if ncf <= 0:
        return 0
    pct = payment / ncf
    if pct <= 0.5:
        return 100
    if pct <= 0.8:
        return 60
    if pct <= 1.0:
        return 20
    return 0


def s_goal(delta_pgrs: float) -> float:
    """100 - min(100, ΔPGRS*3). Continuous form is source of truth."""
    return 100.0 - min(100.0, max(0.0, delta_pgrs) * 3.0)


def s_efr(efr_after: float) -> int:
    """>=6 ->100, 3–6 ->70, 1–3 ->30, <1 ->0."""
    if efr_after >= 6:
        return 100
    if efr_after >= 3:
        return 70
    if efr_after >= 1:
        return 30
    return 0


def s_dti(dti_new: float) -> int:
    """<20 ->100, 20–35 ->70, 35–40 ->40, >40 ->0."""
    if dti_new < 20:
        return 100
    if dti_new < 35:
        return 70
    if dti_new < 40:
        return 40
    return 0
```

```python
# app/modules/advisory/domain/scoring.py
from __future__ import annotations

from dataclasses import dataclass

from app.modules.advisory.domain.subscores import SubScores


@dataclass(frozen=True)
class ScoreWeights:
    cashflow: float = 0.35
    goal: float = 0.35
    efr: float = 0.20
    dti: float = 0.10


def weighted_option_score(sub: SubScores, weights: ScoreWeights) -> float:
    """Deterministic weighted option score in [0,100] (higher = better)."""
    return (
        weights.cashflow * sub.cashflow
        + weights.goal * sub.goal
        + weights.efr * sub.efr
        + weights.dti * sub.dti
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_subscores.py -v`
Expected: PASS (8 tests).

- [ ] **Step 5: Commit**

```bash
git add app/modules/advisory/domain/subscores.py app/modules/advisory/domain/scoring.py tests/unit/test_subscores.py
git commit -m "feat(advisory): add deterministic sub-scores and weighted score"
```

---

## Task 11: Advisory DTOs + RiskScorer port

**Files:**
- Create: `app/modules/advisory/application/__init__.py`, `app/modules/advisory/application/dto.py`, `app/modules/advisory/application/ports.py`
- Test: `tests/unit/test_advisory_dto.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_advisory_dto.py
from app.modules.advisory.application.dto import (
    OptionPacket, OptionScore, ScoringPacket, ScoringResult,
)
from app.modules.advisory.domain.options import PaymentOption, PlanType
from app.modules.advisory.domain.subscores import SubScores


def test_option_packet_holds_metrics_and_flags():
    opt = PaymentOption("full", "Trả thẳng", PlanType.PAY_IN_FULL, None, 0, 15_000_000)
    packet = OptionPacket(
        option=opt, payment=0, ncf_new=1_200_000, dti_new=37.9, efr_after=2.94,
        pgrs_new=100.0, delta_pgrs=0.0,
        subscores=SubScores(100, 100.0, 30, 40), flags=["REQUIRES_EMERGENCY_FUND"],
    )
    assert packet.flags == ["REQUIRES_EMERGENCY_FUND"]
    assert packet.option.id == "full"


def test_scoring_result_round_trips():
    result = ScoringResult(
        options=[OptionScore("full", 52.0, True, "ok", ["cashflow"])],
        best_option_id="full", summary="done", scorer_used="deterministic",
    )
    assert result.best_option_id == "full"
    assert result.options[0].risk_score == 52.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_advisory_dto.py -v`
Expected: FAIL — modules not found.

- [ ] **Step 3: Write the implementations**

```python
# app/modules/advisory/application/dto.py
from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.advisory.domain.options import PaymentOption
from app.modules.advisory.domain.subscores import SubScores


@dataclass
class OptionPacket:
    option: PaymentOption
    payment: int          # monthly payment used for scoring (0 for pay-in-full)
    ncf_new: int
    dti_new: float
    efr_after: float
    pgrs_new: float
    delta_pgrs: float
    subscores: SubScores
    flags: list[str] = field(default_factory=list)


@dataclass
class ScoringPacket:
    profile_id: str
    risk_tolerance: str
    current_ncf: int
    current_dti: float
    current_efr: float
    current_pgrs: float
    item_name: str
    purchase_amount: int
    options: list[OptionPacket]


@dataclass
class OptionScore:
    option_id: str
    risk_score: float        # 0 = safest, 100 = riskiest
    recommended: bool
    explanation: str
    key_factors: list[str] = field(default_factory=list)


@dataclass
class ScoringResult:
    options: list[OptionScore]
    best_option_id: str
    summary: str
    scorer_used: str         # "bedrock" | "deterministic"
```

```python
# app/modules/advisory/application/ports.py
from __future__ import annotations

from typing import Protocol

from app.modules.advisory.application.dto import ScoringPacket, ScoringResult


class RiskScorer(Protocol):
    def score(self, packet: ScoringPacket) -> ScoringResult:
        """Assign a 0–100 risk score per option and choose the best."""
        ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_advisory_dto.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add app/modules/advisory/application tests/unit/test_advisory_dto.py
git commit -m "feat(advisory): add scoring DTOs and RiskScorer port"
```

---

## Task 12: Deterministic scorer (fallback + tests)

**Files:**
- Create: `app/modules/explanation/__init__.py`, `app/modules/explanation/infrastructure/__init__.py`, `app/modules/explanation/infrastructure/deterministic_scorer.py`
- Test: `tests/unit/test_deterministic_scorer.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_deterministic_scorer.py
from app.modules.advisory.application.dto import OptionPacket, ScoringPacket
from app.modules.advisory.domain.options import PaymentOption, PlanType
from app.modules.advisory.domain.scoring import ScoreWeights
from app.modules.advisory.domain.subscores import SubScores
from app.modules.explanation.infrastructure.deterministic_scorer import DeterministicScorer


def _packet() -> ScoringPacket:
    full = PaymentOption("full", "Trả thẳng", PlanType.PAY_IN_FULL, None, 0, 15_000_000)
    inst = PaymentOption("installment_12", "Trả góp 12", PlanType.INSTALLMENT, 12, 1_250_000, 0)
    return ScoringPacket(
        profile_id="p1", risk_tolerance="MEDIUM",
        current_ncf=1_200_000, current_dti=37.9, current_efr=2.94, current_pgrs=100.0,
        item_name="Phone", purchase_amount=15_000_000,
        options=[
            OptionPacket(full, 0, -13_800_000, 37.9, 2.94, 100.0, 0.0,
                         SubScores(100, 100.0, 30, 40), flags=["NEGATIVE_CASHFLOW"]),
            OptionPacket(inst, 1_250_000, -50_000, 46.5, 2.94, 100.0, 8.0,
                         SubScores(20, 76.0, 30, 0), flags=["NEGATIVE_CASHFLOW"]),
        ],
    )


def test_risk_is_100_minus_weighted_score():
    scorer = DeterministicScorer(ScoreWeights())
    result = scorer.score(_packet())
    # full: .35*100+.35*100+.20*30+.10*40 = 35+35+6+4 = 80 -> risk 20
    full = next(o for o in result.options if o.option_id == "full")
    assert full.risk_score == 20.0
    assert result.scorer_used == "deterministic"


def test_best_option_is_lowest_risk():
    result = DeterministicScorer(ScoreWeights()).score(_packet())
    # full risk 20 vs installment_12: .35*20+.35*76+.20*30+.10*0=7+26.6+6+0=39.6 -> risk 60.4
    assert result.best_option_id == "full"


def test_negative_cashflow_option_marked_not_recommended():
    result = DeterministicScorer(ScoreWeights()).score(_packet())
    assert all(o.recommended is False for o in result.options)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_deterministic_scorer.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the implementation**

```python
# app/modules/explanation/infrastructure/deterministic_scorer.py
from __future__ import annotations

from app.modules.advisory.application.dto import (
    OptionPacket, OptionScore, ScoringPacket, ScoringResult,
)
from app.modules.advisory.domain.scoring import ScoreWeights, weighted_option_score

_BLOCKING_FLAGS = {"NEGATIVE_CASHFLOW", "REQUIRES_EMERGENCY_FUND"}


def _factors(packet: OptionPacket) -> list[str]:
    factors: list[str] = []
    if packet.subscores.cashflow >= 60:
        factors.append("dòng tiền an toàn")
    else:
        factors.append("áp lực dòng tiền")
    if packet.delta_pgrs <= 10:
        factors.append("ít ảnh hưởng mục tiêu")
    else:
        factors.append("ảnh hưởng mục tiêu đáng kể")
    if packet.subscores.efr >= 70:
        factors.append("quỹ khẩn cấp ổn")
    if packet.subscores.dti >= 70:
        factors.append("DTI trong ngưỡng an toàn")
    return factors


class DeterministicScorer:
    """Risk = 100 - weighted option score. Higher risk = worse."""

    def __init__(self, weights: ScoreWeights) -> None:
        self._weights = weights

    def score(self, packet: ScoringPacket) -> ScoringResult:
        scores: list[OptionScore] = []
        for opt in packet.options:
            weighted = weighted_option_score(opt.subscores, self._weights)
            risk = round(100.0 - weighted, 1)
            blocked = any(flag in _BLOCKING_FLAGS for flag in opt.flags)
            explanation = (
                f"{opt.option.label}: điểm tổng hợp {weighted:.1f}/100"
                + (" (vi phạm ràng buộc cứng — không khuyến nghị)" if blocked else "")
            )
            scores.append(OptionScore(
                option_id=opt.option.id, risk_score=risk, recommended=not blocked,
                explanation=explanation, key_factors=_factors(opt),
            ))

        # rank: non-blocked first, then ascending risk
        def sort_key(s: OptionScore) -> tuple[int, float]:
            return (0 if s.recommended else 1, s.risk_score)

        ranked = sorted(scores, key=sort_key)
        best = ranked[0].option_id
        summary = f"Phương án rủi ro thấp nhất: {best} (risk {ranked[0].risk_score})."
        return ScoringResult(
            options=scores, best_option_id=best, summary=summary,
            scorer_used="deterministic",
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_deterministic_scorer.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add app/modules/explanation tests/unit/test_deterministic_scorer.py
git commit -m "feat(explanation): add deterministic risk scorer"
```

---

## Task 13: Bedrock scorer (boto3) with fallback

**Files:**
- Create: `app/modules/explanation/schemas.py`, `app/modules/explanation/infrastructure/bedrock_scorer.py`
- Test: `tests/unit/test_bedrock_scorer.py`

- [ ] **Step 1: Write the failing test (stubbed boto3 client)**

```python
# tests/unit/test_bedrock_scorer.py
import json
import pytest

from app.modules.advisory.application.dto import OptionPacket, ScoringPacket
from app.modules.advisory.domain.options import PaymentOption, PlanType
from app.modules.advisory.domain.scoring import ScoreWeights
from app.modules.advisory.domain.subscores import SubScores
from app.modules.explanation.infrastructure.bedrock_scorer import BedrockScorer
from app.modules.explanation.infrastructure.deterministic_scorer import DeterministicScorer


def _packet() -> ScoringPacket:
    inst = PaymentOption("installment_12", "Trả góp 12", PlanType.INSTALLMENT, 12, 1_250_000, 0)
    return ScoringPacket(
        profile_id="p1", risk_tolerance="MEDIUM",
        current_ncf=1_200_000, current_dti=37.9, current_efr=2.94, current_pgrs=100.0,
        item_name="Phone", purchase_amount=15_000_000,
        options=[OptionPacket(inst, 1_250_000, -50_000, 46.5, 2.94, 100.0, 8.0,
                              SubScores(20, 76.0, 30, 0))],
    )


class _StubClient:
    def __init__(self, body: str | None, raise_exc: Exception | None = None):
        self._body = body
        self._raise = raise_exc

    def invoke_model(self, **kwargs):
        if self._raise:
            raise self._raise
        return {"body": _StubBody(self._body)}


class _StubBody:
    def __init__(self, body: str | None):
        self._body = body

    def read(self) -> bytes:
        payload = {"content": [{"type": "text", "text": self._body}]}
        return json.dumps(payload).encode()


def _fallback() -> DeterministicScorer:
    return DeterministicScorer(ScoreWeights())


def test_bedrock_parses_valid_json():
    valid = json.dumps({
        "options": [{"option_id": "installment_12", "risk_score": 55,
                     "recommended": True, "explanation": "ổn", "key_factors": ["x"]}],
        "best_option_id": "installment_12", "summary": "ok",
    })
    scorer = BedrockScorer(client=_StubClient(valid), model_id="m", fallback=_fallback())
    result = scorer.score(_packet())
    assert result.scorer_used == "bedrock"
    assert result.options[0].risk_score == 55


def test_bedrock_malformed_json_falls_back():
    scorer = BedrockScorer(client=_StubClient("not json"), model_id="m", fallback=_fallback())
    result = scorer.score(_packet())
    assert result.scorer_used == "deterministic"


def test_bedrock_client_error_falls_back():
    scorer = BedrockScorer(
        client=_StubClient(None, raise_exc=RuntimeError("boom")),
        model_id="m", fallback=_fallback(),
    )
    result = scorer.score(_packet())
    assert result.scorer_used == "deterministic"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_bedrock_scorer.py -v`
Expected: FAIL — modules not found.

- [ ] **Step 3: Write the implementations**

```python
# app/modules/explanation/schemas.py
from __future__ import annotations

from pydantic import BaseModel, Field


class LLMOptionScore(BaseModel):
    option_id: str
    risk_score: float = Field(ge=0, le=100)
    recommended: bool
    explanation: str
    key_factors: list[str] = Field(default_factory=list)


class LLMScoringResponse(BaseModel):
    options: list[LLMOptionScore]
    best_option_id: str
    summary: str
```

```python
# app/modules/explanation/infrastructure/bedrock_scorer.py
from __future__ import annotations

import json
import logging
from typing import Any, Protocol

from pydantic import ValidationError

from app.modules.advisory.application.dto import (
    OptionScore, ScoringPacket, ScoringResult,
)
from app.modules.advisory.application.ports import RiskScorer
from app.modules.explanation.schemas import LLMScoringResponse

logger = logging.getLogger(__name__)

_SYSTEM = (
    "Bạn là cố vấn tài chính. Dựa trên các chỉ số ĐÃ TÍNH SẴN cho mỗi phương án "
    "thanh toán, hãy chấm điểm RỦI RO mỗi phương án trên thang 0-100 "
    "(0 = an toàn nhất, 100 = rủi ro nhất) và chọn phương án tốt nhất "
    "(rủi ro thấp nhất, không vi phạm ràng buộc cứng). "
    "CHỈ trả về JSON đúng schema, không thêm chữ nào khác."
)


class BedrockClient(Protocol):
    def invoke_model(self, **kwargs: Any) -> Any: ...


def _build_prompt(packet: ScoringPacket) -> str:
    options = [
        {
            "option_id": o.option.id, "label": o.option.label,
            "monthly_payment": o.payment, "ncf_new": o.ncf_new,
            "dti_new": round(o.dti_new, 2), "efr_after": round(o.efr_after, 2),
            "delta_pgrs": round(o.delta_pgrs, 2),
            "subscores": {
                "cashflow": o.subscores.cashflow, "goal": o.subscores.goal,
                "efr": o.subscores.efr, "dti": o.subscores.dti,
            },
            "flags": o.flags,
        }
        for o in packet.options
    ]
    payload = {
        "item": packet.item_name, "amount": packet.purchase_amount,
        "risk_tolerance": packet.risk_tolerance,
        "current": {
            "ncf": packet.current_ncf, "dti": round(packet.current_dti, 2),
            "efr": round(packet.current_efr, 2), "pgrs": round(packet.current_pgrs, 2),
        },
        "options": options,
        "response_schema": {
            "options": [{"option_id": "str", "risk_score": "0-100",
                         "recommended": "bool", "explanation": "str",
                         "key_factors": ["str"]}],
            "best_option_id": "str", "summary": "str",
        },
    }
    return json.dumps(payload, ensure_ascii=False)


class BedrockScorer(RiskScorer):
    def __init__(self, client: BedrockClient, model_id: str, fallback: RiskScorer) -> None:
        self._client = client
        self._model_id = model_id
        self._fallback = fallback

    def score(self, packet: ScoringPacket) -> ScoringResult:
        try:
            text = self._invoke(packet)
            parsed = LLMScoringResponse.model_validate_json(text)
        except (ValidationError, json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.warning("Bedrock response unusable, falling back: %s", exc)
            return self._fallback.score(packet)
        except Exception as exc:  # boto3 ClientError etc.
            logger.warning("Bedrock call failed, falling back: %s", exc)
            return self._fallback.score(packet)

        return ScoringResult(
            options=[
                OptionScore(o.option_id, o.risk_score, o.recommended,
                            o.explanation, o.key_factors)
                for o in parsed.options
            ],
            best_option_id=parsed.best_option_id,
            summary=parsed.summary,
            scorer_used="bedrock",
        )

    def _invoke(self, packet: ScoringPacket) -> str:
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "system": _SYSTEM,
            "messages": [{"role": "user", "content": _build_prompt(packet)}],
        })
        response = self._client.invoke_model(modelId=self._model_id, body=body)
        raw = json.loads(response["body"].read())
        return str(raw["content"][0]["text"])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_bedrock_scorer.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add app/modules/explanation/schemas.py app/modules/explanation/infrastructure/bedrock_scorer.py tests/unit/test_bedrock_scorer.py
git commit -m "feat(explanation): add Bedrock risk scorer with deterministic fallback"
```

---

## Task 14: Advisory orchestration service (EvaluatePurchase)

**Files:**
- Create: `app/modules/advisory/application/services.py`
- Test: `tests/unit/test_evaluate_service.py`

This service ties the engine to the scorer: build current metrics, then per option
recompute metrics with the option's monthly payment, build the packet, score it.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_evaluate_service.py
from datetime import date

from app.core.clock import FixedClock
from app.modules.advisory.application.services import EvaluatePurchaseService
from app.modules.advisory.domain.options import default_plans
from app.modules.advisory.domain.scoring import ScoreWeights
from app.modules.analysis.application.services import AnalysisService
from app.modules.analysis.domain.allocation import EvenAllocation
from app.modules.explanation.infrastructure.deterministic_scorer import DeterministicScorer
from app.modules.goals.domain.entities import Goal, Priority
from app.modules.profiles.domain.entities import Debt, Expense, FinancialProfile, Income
from app.modules.profiles.domain.value_objects import DebtType, ExpenseClass, RiskTolerance


def _profile() -> FinancialProfile:
    return FinancialProfile(
        id="p1",
        income=Income(10_000_000, 3_000_000, 1_000_000, 500_000),
        risk=RiskTolerance.MEDIUM, emergency_fund=20_000_000,
        expenses=[
            Expense("rent", 3_000_000, ExpenseClass.FIXED),
            Expense("food", 3_000_000, ExpenseClass.SEMI_FIXED),
            Expense("transport", 500_000, ExpenseClass.SEMI_FIXED),
            Expense("internet", 300_000, ExpenseClass.FIXED),
            Expense("fun", 1_000_000, ExpenseClass.DISCRETIONARY),
        ],
        debts=[Debt("cc", 2_000_000, None, 30.0, None, DebtType.REVOLVING),
               Debt("bnpl", 1_500_000, 9_000_000, 0.0, 6, DebtType.INSTALLMENT),
               Debt("car", 2_000_000, 100_000_000, 10.0, 50, DebtType.SECURED)],
        goals=[Goal("car", "Car", 300_000_000, date(2027, 12, 1), Priority.HIGH),
               Goal("house", "House", 1_000_000_000, date(2034, 12, 1), Priority.VERY_HIGH),
               Goal("japan", "Japan", 50_000_000, date(2026, 12, 1), Priority.MEDIUM)],
    )


def _service() -> EvaluatePurchaseService:
    analysis = AnalysisService(FixedClock(date(2025, 6, 1)), EvenAllocation())
    return EvaluatePurchaseService(
        analysis=analysis, scorer=DeterministicScorer(ScoreWeights()),
    )


def test_evaluate_returns_one_score_per_option():
    result = _service().evaluate(_profile(), "Phone", 15_000_000, default_plans())
    assert {o.option_id for o in result.scoring.options} == {
        "full", "installment_3", "installment_6", "installment_12",
    }
    assert result.metrics.ncf == 1_200_000


def test_evaluate_flags_negative_cashflow_options():
    result = _service().evaluate(_profile(), "Phone", 15_000_000, default_plans())
    # 15,000,000 / 3 = 5,000,000 monthly > NCF 1,200,000 -> negative cashflow
    inst3 = next(p for p in result.packets if p.option.id == "installment_3")
    assert "NEGATIVE_CASHFLOW" in inst3.flags


def test_evaluate_pay_in_full_requires_emergency_fund_flag_when_cash_short():
    # purchase 150,000,000 > cash; pay-in-full should flag emergency-fund risk
    result = _service().evaluate(_profile(), "Car", 150_000_000, default_plans())
    full = next(p for p in result.packets if p.option.id == "full")
    assert "REQUIRES_EMERGENCY_FUND" in full.flags
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_evaluate_service.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the implementation**

```python
# app/modules/advisory/application/services.py
from __future__ import annotations

from dataclasses import dataclass

from app.modules.advisory.application.dto import OptionPacket, ScoringPacket, ScoringResult
from app.modules.advisory.application.ports import RiskScorer
from app.modules.advisory.domain.options import PaymentOption, PlanSpec, PlanType, generate_options
from app.modules.advisory.domain.subscores import SubScores, s_cashflow, s_dti, s_efr, s_goal
from app.modules.analysis.application.services import AnalysisService
from app.modules.analysis.domain.results import ProfileMetrics
from app.modules.profiles.domain.entities import FinancialProfile
from app.modules.profiles.domain.value_objects import AssetType


@dataclass
class EvaluationResult:
    metrics: ProfileMetrics
    packets: list[OptionPacket]
    scoring: ScoringResult


class EvaluatePurchaseService:
    def __init__(self, analysis: AnalysisService, scorer: RiskScorer) -> None:
        self._analysis = analysis
        self._scorer = scorer

    def evaluate(
        self, profile: FinancialProfile, item_name: str, amount: int,
        plans: list[PlanSpec],
    ) -> EvaluationResult:
        current = self._analysis.analyze(profile)
        liquid_cash = sum(
            a.value for a in profile.assets
            if a.type in (AssetType.CASH, AssetType.SAVINGS)
        )

        packets = [
            self._build_packet(profile, current, option, amount, liquid_cash)
            for option in generate_options(amount, plans)
        ]
        packet = ScoringPacket(
            profile_id=profile.id, risk_tolerance=profile.risk.value,
            current_ncf=current.ncf, current_dti=current.dti,
            current_efr=current.efr, current_pgrs=current.pgrs,
            item_name=item_name, purchase_amount=amount, options=packets,
        )
        scoring = self._scorer.score(packet)
        return EvaluationResult(metrics=current, packets=packets, scoring=scoring)

    def _build_packet(
        self, profile: FinancialProfile, current: ProfileMetrics,
        option: PaymentOption, amount: int, liquid_cash: int,
    ) -> OptionPacket:
        monthly = option.monthly_payment
        with_payment = self._analysis.analyze(profile, new_payment=monthly)
        flags: list[str] = []
        if with_payment.ncf < 0:
            flags.append("NEGATIVE_CASHFLOW")

        if option.type == PlanType.PAY_IN_FULL and option.upfront > liquid_cash:
            # paying in full would force drawing the emergency fund
            flags.append("REQUIRES_EMERGENCY_FUND")

        sub = SubScores(
            cashflow=s_cashflow(monthly, current.ncf),
            goal=s_goal(with_payment.pgrs - current.pgrs),
            efr=s_efr(with_payment.efr),
            dti=s_dti(with_payment.dti),
        )
        return OptionPacket(
            option=option, payment=monthly, ncf_new=with_payment.ncf,
            dti_new=with_payment.dti, efr_after=with_payment.efr,
            pgrs_new=with_payment.pgrs, delta_pgrs=with_payment.pgrs - current.pgrs,
            subscores=sub, flags=flags,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_evaluate_service.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add app/modules/advisory/application/services.py tests/unit/test_evaluate_service.py
git commit -m "feat(advisory): add EvaluatePurchase orchestration service"
```

---

## Task 15: Profile repository port + in-memory adapter

**Files:**
- Create: `app/modules/profiles/application/__init__.py`, `app/modules/profiles/application/ports.py`
- Create: `app/modules/profiles/infrastructure/__init__.py`, `app/modules/profiles/infrastructure/memory_repository.py`
- Create: `app/core/errors.py`
- Test: `tests/unit/test_memory_repository.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_memory_repository.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_memory_repository.py -v`
Expected: FAIL — modules not found.

- [ ] **Step 3: Write the implementations**

```python
# app/core/errors.py
from __future__ import annotations


class DomainError(Exception):
    """Base for domain errors."""


class ProfileNotFound(DomainError):
    def __init__(self, profile_id: str) -> None:
        super().__init__(f"Profile not found: {profile_id}")
        self.profile_id = profile_id


class GoalNotFound(DomainError):
    def __init__(self, goal_id: str) -> None:
        super().__init__(f"Goal not found: {goal_id}")
        self.goal_id = goal_id


class InvalidInput(DomainError):
    pass
```

```python
# app/modules/profiles/application/ports.py
from __future__ import annotations

from typing import Protocol

from app.modules.profiles.domain.entities import FinancialProfile


class ProfileRepository(Protocol):
    async def add(self, profile: FinancialProfile) -> None: ...
    async def get(self, profile_id: str) -> FinancialProfile: ...
    async def update(self, profile: FinancialProfile) -> None: ...
```

```python
# app/modules/profiles/infrastructure/memory_repository.py
from __future__ import annotations

from app.core.errors import ProfileNotFound
from app.modules.profiles.domain.entities import FinancialProfile


class InMemoryProfileRepository:
    def __init__(self) -> None:
        self._store: dict[str, FinancialProfile] = {}

    async def add(self, profile: FinancialProfile) -> None:
        self._store[profile.id] = profile

    async def get(self, profile_id: str) -> FinancialProfile:
        if profile_id not in self._store:
            raise ProfileNotFound(profile_id)
        return self._store[profile_id]

    async def update(self, profile: FinancialProfile) -> None:
        if profile.id not in self._store:
            raise ProfileNotFound(profile.id)
        self._store[profile.id] = profile
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_memory_repository.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add app/core/errors.py app/modules/profiles/application app/modules/profiles/infrastructure tests/unit/test_memory_repository.py
git commit -m "feat(profiles): add repository port and in-memory adapter"
```

---

## Task 16: Settings + composition root (config)

**Files:**
- Create: `app/core/config.py`
- Test: `tests/unit/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_config.py
from app.core.config import Settings


def test_defaults_use_memory_and_disabled_bedrock(monkeypatch):
    monkeypatch.delenv("PERSISTENCE", raising=False)
    monkeypatch.delenv("BEDROCK_ENABLED", raising=False)
    s = Settings(_env_file=None)
    assert s.persistence == "memory"
    assert s.bedrock_enabled is False
    assert s.allocation_strategy in ("weighted", "even")


def test_weights_loaded():
    s = Settings(_env_file=None)
    assert abs(s.score_weight_cashflow + s.score_weight_goal
               + s.score_weight_efr + s.score_weight_dti - 1.0) < 1e-9
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_config.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the implementation**

```python
# app/core/config.py
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

    score_weight_cashflow: float = 0.35
    score_weight_goal: float = 0.35
    score_weight_efr: float = 0.20
    score_weight_dti: float = 0.10


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_config.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add app/core/config.py tests/unit/test_config.py
git commit -m "feat(core): add Settings with env-driven config"
```

---

## Task 17: API layer + app factory (in-memory wiring)

**Files:**
- Create: `app/modules/profiles/api/__init__.py`, `app/modules/profiles/api/schemas.py`, `app/modules/profiles/api/router.py`
- Create: `app/modules/analysis/api/__init__.py`, `app/modules/analysis/api/schemas.py`, `app/modules/analysis/api/router.py`
- Create: `app/modules/advisory/api/__init__.py`, `app/modules/advisory/api/schemas.py`, `app/modules/advisory/api/router.py`
- Create: `app/main.py`, `app/dependencies.py`
- Test: `tests/integration/__init__.py`, `tests/integration/test_api.py`

- [ ] **Step 1: Write the failing integration test**

```python
# tests/integration/test_api.py
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture
async def client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _profile_body() -> dict:
    return {
        "id": "p1",
        "income": {"salary": 10_000_000, "secondary": 3_000_000,
                   "avg_bonus_monthly": 1_000_000, "passive": 500_000},
        "risk": "MEDIUM", "emergency_fund": 20_000_000,
        "expenses": [
            {"category": "rent", "amount": 3_000_000, "classification": "FIXED"},
            {"category": "food", "amount": 3_000_000, "classification": "SEMI_FIXED"},
            {"category": "transport", "amount": 500_000, "classification": "SEMI_FIXED"},
            {"category": "internet", "amount": 300_000, "classification": "FIXED"},
            {"category": "fun", "amount": 1_000_000, "classification": "DISCRETIONARY"},
        ],
        "debts": [
            {"name": "cc", "monthly_payment": 2_000_000, "balance": None,
             "apr": 30.0, "months_remaining": None, "debt_type": "REVOLVING"},
            {"name": "bnpl", "monthly_payment": 1_500_000, "balance": 9_000_000,
             "apr": 0.0, "months_remaining": 6, "debt_type": "INSTALLMENT"},
            {"name": "car", "monthly_payment": 2_000_000, "balance": 100_000_000,
             "apr": 10.0, "months_remaining": 50, "debt_type": "SECURED"},
        ],
        "assets": [{"type": "CASH", "value": 20_000_000, "liquidity": "HIGH"}],
        "goals": [
            {"id": "car", "name": "Car", "target_amount": 300_000_000,
             "deadline": "2027-12-01", "priority": "HIGH", "savings_allocated": 0},
        ],
    }


async def test_create_and_analyze_profile(client):
    r = await client.post("/profiles", json=_profile_body())
    assert r.status_code == 201

    a = await client.get("/profiles/p1/analysis")
    assert a.status_code == 200
    body = a.json()
    assert body["ncf"] == 1_200_000
    assert round(body["dti"], 2) == 37.93
    assert body["dti_band"] == "WARNING"


async def test_analyze_missing_profile_returns_404(client):
    r = await client.get("/profiles/ghost/analysis")
    assert r.status_code == 404


async def test_evaluate_purchase(client):
    await client.post("/profiles", json=_profile_body())
    r = await client.post("/advisory/evaluate", json={
        "profile_id": "p1", "item_name": "Phone", "purchase_amount": 15_000_000,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["scorer_used"] == "deterministic"
    assert len(body["options"]) == 4
    assert "best_option_id" in body
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_api.py -v`
Expected: FAIL — `app.main` not found. Create `tests/integration/__init__.py` (empty).

- [ ] **Step 3: Write the API schemas**

```python
# app/modules/profiles/api/schemas.py
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class IncomeIn(BaseModel):
    salary: int = Field(ge=0)
    secondary: int = Field(default=0, ge=0)
    avg_bonus_monthly: int = Field(default=0, ge=0)
    passive: int = Field(default=0, ge=0)


class ExpenseIn(BaseModel):
    category: str
    amount: int = Field(ge=0)
    classification: str


class DebtIn(BaseModel):
    name: str
    monthly_payment: int = Field(ge=0)
    balance: int | None = None
    apr: float = 0.0
    months_remaining: int | None = None
    debt_type: str


class AssetIn(BaseModel):
    type: str
    value: int = Field(ge=0)
    liquidity: str


class GoalIn(BaseModel):
    id: str
    name: str
    target_amount: int = Field(ge=0)
    deadline: date
    priority: str
    savings_allocated: int = Field(default=0, ge=0)


class ProfileIn(BaseModel):
    id: str
    income: IncomeIn
    risk: str
    emergency_fund: int = Field(default=0, ge=0)
    expenses: list[ExpenseIn] = Field(default_factory=list)
    debts: list[DebtIn] = Field(default_factory=list)
    assets: list[AssetIn] = Field(default_factory=list)
    goals: list[GoalIn] = Field(default_factory=list)
```

```python
# app/modules/analysis/api/schemas.py
from __future__ import annotations

from pydantic import BaseModel

from app.modules.analysis.domain.results import ProfileMetrics


class GoalMetricOut(BaseModel):
    goal_id: str
    name: str
    gap: int
    monthly_allocated: int
    gat: float
    delay: float
    grs: float
    months_remaining: int


class MetricsOut(BaseModel):
    ncf: int
    dti: float
    dti_band: str
    saving_rate: float
    efr: float
    pgrs: float
    goals: list[GoalMetricOut]
    flags: list[str]

    @classmethod
    def from_domain(cls, m: ProfileMetrics) -> "MetricsOut":
        return cls(
            ncf=m.ncf, dti=m.dti, dti_band=m.dti_band.value,
            saving_rate=m.saving_rate, efr=m.efr, pgrs=m.pgrs,
            goals=[GoalMetricOut(**g.__dict__) for g in m.goals],
            flags=m.flags,
        )
```

```python
# app/modules/advisory/api/schemas.py
from __future__ import annotations

from pydantic import BaseModel, Field


class PlanIn(BaseModel):
    type: str                      # "PAY_IN_FULL" | "INSTALLMENT"
    months: int | None = None
    apr: float = 0.0


class EvaluateIn(BaseModel):
    profile_id: str
    item_name: str
    purchase_amount: int = Field(gt=0)
    candidate_plans: list[PlanIn] | None = None


class OptionScoreOut(BaseModel):
    option_id: str
    risk_score: float
    recommended: bool
    explanation: str
    key_factors: list[str]
    monthly_payment: int
    ncf_new: int
    dti_new: float
    efr_after: float
    delta_pgrs: float
    flags: list[str]


class EvaluateOut(BaseModel):
    best_option_id: str
    summary: str
    scorer_used: str
    options: list[OptionScoreOut]
```

- [ ] **Step 4: Write the mappers (domain <-> API) and dependencies**

```python
# app/modules/profiles/api/mappers.py
from __future__ import annotations

from app.modules.goals.domain.entities import Goal, Priority
from app.modules.profiles.api.schemas import ProfileIn
from app.modules.profiles.domain.entities import (
    Asset, Debt, Expense, FinancialProfile, Income,
)
from app.modules.profiles.domain.value_objects import (
    AssetType, DebtType, ExpenseClass, Liquidity, RiskTolerance,
)


def to_domain(body: ProfileIn) -> FinancialProfile:
    return FinancialProfile(
        id=body.id,
        income=Income(**body.income.model_dump()),
        risk=RiskTolerance(body.risk),
        emergency_fund=body.emergency_fund,
        expenses=[Expense(e.category, e.amount, ExpenseClass(e.classification))
                  for e in body.expenses],
        debts=[Debt(d.name, d.monthly_payment, d.balance, d.apr,
                    d.months_remaining, DebtType(d.debt_type)) for d in body.debts],
        assets=[Asset(AssetType(a.type), a.value, Liquidity(a.liquidity))
                for a in body.assets],
        goals=[Goal(g.id, g.name, g.target_amount, g.deadline,
                    Priority[g.priority], g.savings_allocated) for g in body.goals],
    )
```

```python
# app/dependencies.py
from __future__ import annotations

import boto3

from app.core.clock import SystemClock
from app.core.config import Settings, get_settings
from app.modules.advisory.application.ports import RiskScorer
from app.modules.advisory.application.services import EvaluatePurchaseService
from app.modules.advisory.domain.scoring import ScoreWeights
from app.modules.analysis.application.services import AnalysisService
from app.modules.analysis.domain.allocation import get_strategy
from app.modules.explanation.infrastructure.bedrock_scorer import BedrockScorer
from app.modules.explanation.infrastructure.deterministic_scorer import DeterministicScorer
from app.modules.profiles.application.ports import ProfileRepository
from app.modules.profiles.infrastructure.memory_repository import InMemoryProfileRepository

# Single in-memory repo instance for the app lifetime (MVP default).
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
```

- [ ] **Step 5: Write the routers**

```python
# app/modules/profiles/api/router.py
from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.dependencies import get_analysis_service, get_repository
from app.modules.analysis.api.schemas import MetricsOut
from app.modules.analysis.application.services import AnalysisService
from app.modules.profiles.api.mappers import to_domain
from app.modules.profiles.api.schemas import ProfileIn
from app.modules.profiles.application.ports import ProfileRepository

router = APIRouter(tags=["profiles"])


@router.post("/profiles", status_code=status.HTTP_201_CREATED)
async def create_profile(
    body: ProfileIn, repo: ProfileRepository = Depends(get_repository)
) -> dict[str, str]:
    await repo.add(to_domain(body))
    return {"id": body.id}


@router.get("/profiles/{profile_id}/analysis", response_model=MetricsOut)
async def analyze_profile(
    profile_id: str,
    repo: ProfileRepository = Depends(get_repository),
    analysis: AnalysisService = Depends(get_analysis_service),
) -> MetricsOut:
    profile = await repo.get(profile_id)
    return MetricsOut.from_domain(analysis.analyze(profile))
```

```python
# app/modules/advisory/api/router.py
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_evaluate_service, get_repository
from app.modules.advisory.api.schemas import EvaluateIn, EvaluateOut, OptionScoreOut
from app.modules.advisory.application.services import EvaluatePurchaseService
from app.modules.advisory.domain.options import PlanSpec, PlanType, default_plans
from app.modules.profiles.application.ports import ProfileRepository

router = APIRouter(tags=["advisory"])


@router.post("/advisory/evaluate", response_model=EvaluateOut)
async def evaluate(
    body: EvaluateIn,
    repo: ProfileRepository = Depends(get_repository),
    service: EvaluatePurchaseService = Depends(get_evaluate_service),
) -> EvaluateOut:
    profile = await repo.get(body.profile_id)
    plans = (
        [PlanSpec(PlanType(p.type), p.months, p.apr) for p in body.candidate_plans]
        if body.candidate_plans else default_plans()
    )
    result = service.evaluate(profile, body.item_name, body.purchase_amount, plans)
    by_id = {p.option.id: p for p in result.packets}
    options = [
        OptionScoreOut(
            option_id=s.option_id, risk_score=s.risk_score, recommended=s.recommended,
            explanation=s.explanation, key_factors=s.key_factors,
            monthly_payment=by_id[s.option_id].payment,
            ncf_new=by_id[s.option_id].ncf_new, dti_new=by_id[s.option_id].dti_new,
            efr_after=by_id[s.option_id].efr_after,
            delta_pgrs=by_id[s.option_id].delta_pgrs, flags=by_id[s.option_id].flags,
        )
        for s in result.scoring.options
    ]
    return EvaluateOut(
        best_option_id=result.scoring.best_option_id, summary=result.scoring.summary,
        scorer_used=result.scoring.scorer_used, options=options,
    )
```

- [ ] **Step 6: Write the app factory with error handlers**

```python
# app/main.py
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.errors import DomainError, GoalNotFound, ProfileNotFound
from app.modules.advisory.api.router import router as advisory_router
from app.modules.profiles.api.router import router as profiles_router


def create_app() -> FastAPI:
    app = FastAPI(title="BNPL Assistant", version="0.1.0")
    app.include_router(profiles_router)
    app.include_router(advisory_router)

    @app.exception_handler(ProfileNotFound)
    @app.exception_handler(GoalNotFound)
    async def not_found(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(DomainError)
    async def domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `pytest tests/integration/test_api.py -v`
Expected: PASS (3 tests). Then `pytest -q` (whole suite) — all green.

- [ ] **Step 8: Commit**

```bash
git add app/main.py app/dependencies.py app/modules/profiles/api app/modules/analysis/api app/modules/advisory/api tests/integration
git commit -m "feat(api): add profiles + advisory routers and app factory (in-memory)"
```

---

## Task 18: Postgres persistence adapter (approved production store)

**Files:**
- Create: `app/core/database.py`
- Create: `app/modules/profiles/infrastructure/models.py`, `app/modules/profiles/infrastructure/sqlalchemy_repository.py`
- Create: `alembic.ini`, `alembic/env.py`, `alembic/versions/0001_init.py`
- Create: `docker-compose.yml`
- Test: `tests/integration/test_sqlalchemy_repository.py` (skipped if `DATABASE_URL_TEST` unset)

> This adapter implements the same `ProfileRepository` port from Task 15. No core
> or API code changes — only `get_repository()` switches when `PERSISTENCE=postgres`.

- [ ] **Step 1: Write the failing test (DB-gated)**

```python
# tests/integration/test_sqlalchemy_repository.py
import os
import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL_TEST"), reason="no test database configured"
)


@pytest.fixture
async def repo():
    from app.core.database import build_engine, build_sessionmaker, Base
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
    from app.modules.profiles.domain.entities import FinancialProfile, Income, Expense
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
```

- [ ] **Step 2: Run test to verify it fails (or skips)**

Run: `pytest tests/integration/test_sqlalchemy_repository.py -v`
Expected: SKIP if no `DATABASE_URL_TEST`; otherwise FAIL — `app.core.database` not found.

- [ ] **Step 3: Write the database module**

```python
# app/core/database.py
from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def build_engine(url: str) -> AsyncEngine:
    return create_async_engine(url, future=True)


def build_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
```

- [ ] **Step 4: Write the ORM models**

```python
# app/modules/profiles/infrastructure/models.py
from __future__ import annotations

from datetime import date

from sqlalchemy import BigInteger, Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProfileModel(Base):
    __tablename__ = "financial_profiles"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    salary: Mapped[int] = mapped_column(BigInteger)
    secondary: Mapped[int] = mapped_column(BigInteger, default=0)
    avg_bonus_monthly: Mapped[int] = mapped_column(BigInteger, default=0)
    passive: Mapped[int] = mapped_column(BigInteger, default=0)
    emergency_fund: Mapped[int] = mapped_column(BigInteger, default=0)
    risk: Mapped[str] = mapped_column(String)

    expenses: Mapped[list["ExpenseModel"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin")
    debts: Mapped[list["DebtModel"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin")
    assets: Mapped[list["AssetModel"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin")
    goals: Mapped[list["GoalModel"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin")


class ExpenseModel(Base):
    __tablename__ = "expenses"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_id: Mapped[str] = mapped_column(ForeignKey("financial_profiles.id"), index=True)
    category: Mapped[str] = mapped_column(String)
    amount: Mapped[int] = mapped_column(BigInteger)
    classification: Mapped[str] = mapped_column(String)


class DebtModel(Base):
    __tablename__ = "debts"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_id: Mapped[str] = mapped_column(ForeignKey("financial_profiles.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    monthly_payment: Mapped[int] = mapped_column(BigInteger)
    balance: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    apr: Mapped[float] = mapped_column(Float, default=0.0)
    months_remaining: Mapped[int | None] = mapped_column(nullable=True)
    debt_type: Mapped[str] = mapped_column(String)


class AssetModel(Base):
    __tablename__ = "assets"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_id: Mapped[str] = mapped_column(ForeignKey("financial_profiles.id"), index=True)
    type: Mapped[str] = mapped_column(String)
    value: Mapped[int] = mapped_column(BigInteger)
    liquidity: Mapped[str] = mapped_column(String)


class GoalModel(Base):
    __tablename__ = "goals"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    profile_id: Mapped[str] = mapped_column(ForeignKey("financial_profiles.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    target_amount: Mapped[int] = mapped_column(BigInteger)
    deadline: Mapped[date] = mapped_column(Date)
    priority: Mapped[str] = mapped_column(String)
    savings_allocated: Mapped[int] = mapped_column(BigInteger, default=0)
```

- [ ] **Step 5: Write the SQLAlchemy repository (domain mapping)**

```python
# app/modules/profiles/infrastructure/sqlalchemy_repository.py
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.errors import ProfileNotFound
from app.modules.goals.domain.entities import Goal, Priority
from app.modules.profiles.domain.entities import (
    Asset, Debt, Expense, FinancialProfile, Income,
)
from app.modules.profiles.domain.value_objects import (
    AssetType, DebtType, ExpenseClass, Liquidity, RiskTolerance,
)
from app.modules.profiles.infrastructure.models import (
    AssetModel, DebtModel, ExpenseModel, GoalModel, ProfileModel,
)


def _to_model(p: FinancialProfile) -> ProfileModel:
    return ProfileModel(
        id=p.id, salary=p.income.salary, secondary=p.income.secondary,
        avg_bonus_monthly=p.income.avg_bonus_monthly, passive=p.income.passive,
        emergency_fund=p.emergency_fund, risk=p.risk.value,
        expenses=[ExpenseModel(category=e.category, amount=e.amount,
                               classification=e.classification.value) for e in p.expenses],
        debts=[DebtModel(name=d.name, monthly_payment=d.monthly_payment, balance=d.balance,
                         apr=d.apr, months_remaining=d.months_remaining,
                         debt_type=d.debt_type.value) for d in p.debts],
        assets=[AssetModel(type=a.type.value, value=a.value, liquidity=a.liquidity.value)
                for a in p.assets],
        goals=[GoalModel(id=g.id, name=g.name, target_amount=g.target_amount,
                         deadline=g.deadline, priority=g.priority.name,
                         savings_allocated=g.savings_allocated) for g in p.goals],
    )


def _to_domain(m: ProfileModel) -> FinancialProfile:
    return FinancialProfile(
        id=m.id,
        income=Income(m.salary, m.secondary, m.avg_bonus_monthly, m.passive),
        risk=RiskTolerance(m.risk), emergency_fund=m.emergency_fund,
        expenses=[Expense(e.category, e.amount, ExpenseClass(e.classification))
                  for e in m.expenses],
        debts=[Debt(d.name, d.monthly_payment, d.balance, d.apr,
                    d.months_remaining, DebtType(d.debt_type)) for d in m.debts],
        assets=[Asset(AssetType(a.type), a.value, Liquidity(a.liquidity)) for a in m.assets],
        goals=[Goal(g.id, g.name, g.target_amount, g.deadline,
                    Priority[g.priority], g.savings_allocated) for g in m.goals],
    )


class SqlAlchemyProfileRepository:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker

    async def add(self, profile: FinancialProfile) -> None:
        async with self._sessionmaker() as session:
            session.add(_to_model(profile))
            await session.commit()

    async def get(self, profile_id: str) -> FinancialProfile:
        async with self._sessionmaker() as session:
            model = await session.get(ProfileModel, profile_id)
            if model is None:
                raise ProfileNotFound(profile_id)
            return _to_domain(model)

    async def update(self, profile: FinancialProfile) -> None:
        async with self._sessionmaker() as session:
            existing = await session.get(ProfileModel, profile.id)
            if existing is None:
                raise ProfileNotFound(profile.id)
            await session.delete(existing)
            await session.flush()
            session.add(_to_model(profile))
            await session.commit()
```

- [ ] **Step 6: Add Alembic + docker-compose**

Create `docker-compose.yml`:

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: bnpl
      POSTGRES_PASSWORD: bnpl
      POSTGRES_DB: bnpl
    ports:
      - "5432:5432"
```

Run: `alembic init alembic`, then set `sqlalchemy.url` handling in `alembic/env.py`
to import `Base.metadata` from `app.core.database` and all models, reading the URL
from `DATABASE_URL`. Generate the initial migration:

Run: `alembic revision --autogenerate -m "init"` then `alembic upgrade head`.
Expected: tables created.

- [ ] **Step 7: Wire the switch in `app/dependencies.py`**

Replace the `_repo`/`get_repository` section with:

```python
from app.core.database import build_engine, build_sessionmaker
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
```

- [ ] **Step 8: Run tests**

Run: `pytest -q` (Postgres test skips without `DATABASE_URL_TEST`).
With a DB: `docker compose up -d` then
`DATABASE_URL_TEST=postgresql+asyncpg://bnpl:bnpl@localhost:5432/bnpl pytest tests/integration/test_sqlalchemy_repository.py -v`
Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add app/core/database.py app/modules/profiles/infrastructure/models.py app/modules/profiles/infrastructure/sqlalchemy_repository.py app/dependencies.py docker-compose.yml alembic.ini alembic tests/integration/test_sqlalchemy_repository.py
git commit -m "feat(profiles): add Postgres SQLAlchemy repository adapter"
```

---

## Task 19: Ingestion — CSV summaries → profile seeding

**Files:**
- Create: `app/modules/ingestion/__init__.py`, `app/modules/ingestion/application/__init__.py`, `app/modules/ingestion/application/ports.py`, `app/modules/ingestion/application/services.py`
- Create: `app/modules/ingestion/infrastructure/__init__.py`, `app/modules/ingestion/infrastructure/csv_source.py`
- Test: `tests/unit/test_ingestion.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_ingestion.py
from app.modules.ingestion.application.services import CifSeed, derive_seed
from app.modules.ingestion.application.ports import CifSummary


def test_derive_seed_from_latest_month():
    summaries = [
        CifSummary(cif="100", month="2025-01", income=10_000_000,
                   expense=4_000_000, debt_payment=1_000_000),
        CifSummary(cif="100", month="2025-02", income=12_000_000,
                   expense=5_000_000, debt_payment=2_000_000),
    ]
    seed = derive_seed("100", summaries, strategy="latest")
    assert seed == CifSeed(cif="100", income=12_000_000,
                           expense=5_000_000, debt_payment=2_000_000)


def test_derive_seed_average():
    summaries = [
        CifSummary("100", "2025-01", 10_000_000, 4_000_000, 1_000_000),
        CifSummary("100", "2025-02", 12_000_000, 6_000_000, 3_000_000),
    ]
    seed = derive_seed("100", summaries, strategy="average")
    assert seed == CifSeed("100", 11_000_000, 5_000_000, 2_000_000)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_ingestion.py -v`
Expected: FAIL — modules not found.

- [ ] **Step 3: Write the implementations**

```python
# app/modules/ingestion/application/ports.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CifSummary:
    cif: str
    month: str            # "YYYY-MM"
    income: int
    expense: int
    debt_payment: int


class SummarySource(Protocol):
    def load(self, path: str) -> list[CifSummary]:
        """Read summary_by_cif_month.csv into CifSummary rows."""
        ...
```

```python
# app/modules/ingestion/application/services.py
from __future__ import annotations

from dataclasses import dataclass

from app.modules.ingestion.application.ports import CifSummary


@dataclass(frozen=True)
class CifSeed:
    cif: str
    income: int
    expense: int
    debt_payment: int


def derive_seed(cif: str, summaries: list[CifSummary], strategy: str = "latest") -> CifSeed:
    rows = sorted((s for s in summaries if s.cif == cif), key=lambda s: s.month)
    if not rows:
        raise ValueError(f"no summary rows for cif {cif}")
    if strategy == "average":
        n = len(rows)
        return CifSeed(
            cif=cif,
            income=sum(r.income for r in rows) // n,
            expense=sum(r.expense for r in rows) // n,
            debt_payment=sum(r.debt_payment for r in rows) // n,
        )
    latest = rows[-1]
    return CifSeed(cif, latest.income, latest.expense, latest.debt_payment)
```

```python
# app/modules/ingestion/infrastructure/csv_source.py
from __future__ import annotations

import pandas as pd

from app.modules.ingestion.application.ports import CifSummary


class CsvSummarySource:
    def load(self, path: str) -> list[CifSummary]:
        df = pd.read_csv(path, dtype={"CIF_NO": str})
        return [
            CifSummary(
                cif=row["CIF_NO"], month=row["MONTH"],
                income=int(row["total_income"]),
                expense=int(row["total_expense"]),
                debt_payment=int(row["total_debt_payment"]),
            )
            for _, row in df.iterrows()
        ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_ingestion.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add app/modules/ingestion tests/unit/test_ingestion.py
git commit -m "feat(ingestion): derive profile seed from CIF monthly summaries"
```

---

## Task 20: README, lint/type gate, final verification

**Files:**
- Create/Modify: `README.md`

- [ ] **Step 1: Write `README.md`**

````markdown
# BNPL Assistant

Personal-finance advisory MVP. A deterministic engine computes financial-health
metrics; an LLM (AWS Bedrock) assigns 0–100 risk scores to payment options, with
a deterministic fallback.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
```

## Run

```bash
uvicorn app.main:app --reload
# http://localhost:8000/docs
```

Default persistence is in-memory (no infra). For Postgres:

```bash
docker compose up -d
# set PERSISTENCE=postgres in .env, then:
alembic upgrade head
```

## Test

```bash
ruff check . && mypy app && pytest -q
```

## Key endpoints

- `POST /profiles` — create a financial profile
- `GET /profiles/{id}/analysis` — NCF, DTI, saving rate, EFR, per-goal GRS, PGRS
- `POST /advisory/evaluate` — rank payment options for a purchase + explanation

## Config (.env)

| Key | Default | Meaning |
|---|---|---|
| `PERSISTENCE` | `memory` | `memory` or `postgres` |
| `BEDROCK_ENABLED` | `false` | use Bedrock scorer; else deterministic |
| `ALLOCATION_STRATEGY` | `weighted` | `weighted` or `even` NCF split |
````

- [ ] **Step 2: Run the full gate**

Run: `ruff check . && mypy app && pytest -q`
Expected: ruff clean; mypy no errors; all tests pass.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add README with setup, run, and test instructions"
```

---

## Self-review checklist (completed during planning)

- **Spec coverage:** Income/expense/debt/assets/EF/risk (Task 4); goals + priority weight + dynamic months_remaining (Task 4); NCF/DTI/SavingRate/EFR/GAT/GoalGap/Delay/GRS/PGRS (Task 5); DTI bands (Task 6); allocation incl. edge cases (Tasks 7–8); NCF<0 / overdue / zero-allocation edge cases (Task 8); payment options (Task 9); 4 sub-scores (Task 10); LLM scorer + deterministic fallback (Tasks 12–13); evaluate orchestration incl. hard-rule flags (Task 14); persistence both adapters (Tasks 15, 18); CSV ingestion (Task 19); API + config + errors (Tasks 16–17, 20).
- **EFR clarification:** `essential_expense` excludes discretionary per the formula → EFR golden = 2.94 (not the spec's text 2.56, which mistakenly divided by total). Documented in Task 4.
- **Risk convention:** 0 = safest, 100 = riskiest; best = lowest risk among non-blocked options (Tasks 12–14).
- **Type consistency:** `SubScores(cashflow,goal,efr,dti)`, `OptionPacket`, `ScoringPacket`, `ScoringResult`, `ProfileMetrics`, `RiskScorer.score`, `ProfileRepository.{add,get,update}` referenced identically across tasks.

---

## Execution handoff

Plan complete. Two execution options:

1. **Subagent-Driven (recommended)** — a fresh subagent per task, review between tasks.
2. **Inline Execution** — execute tasks in this session with checkpoints.
