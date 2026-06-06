# BNPL Assistant — Design Spec

**Version:** 1.0
**Date:** 2026-06-06
**Status:** Draft — awaiting user review

---

## 1. Purpose

A personal-finance advisory MVP ("BNPL Assistant"). Given a user's financial
profile (income, expenses, debts, assets, emergency fund, goals, risk
tolerance), the system:

1. Computes objective financial-health metrics deterministically.
2. For a proposed purchase, generates candidate payment plans (pay-in-full /
   installment 3 / 6 / 12 months), scores each, and ranks them.
3. Has an LLM (AWS Bedrock) assign a 0–100 **risk score** per option and
   explain the recommendation in natural language.

It builds on the existing `transaction_classifier.py`, which turns the 6-month
banking simulation into per-CIF summaries (income / expense / debt / net
cashflow). Those summaries can seed a profile; the user can also enter or
override data manually.

## 2. Architecture

**Clean Architecture inside a Modular Monolith.** One deployable FastAPI app.
Each module is a bounded context with four layers; dependencies point inward
only (domain depends on nothing).

```
domain          pure entities, value objects, formulas — no I/O, no frameworks
  ^
application     use cases, DTOs, ports (interfaces)
  ^
infrastructure  SQLAlchemy repositories, boto3 Bedrock adapter, CSV reader
  ^
api             FastAPI routers + Pydantic request/response schemas
```

### 2.1 Directory layout

```
app/
  main.py                       # app factory; registers routers; wires DI
  core/
    config.py                   # pydantic-settings (env-driven)
    database.py                 # async SQLAlchemy engine/session, Base
    money.py                    # VND = int; rounding, parsing, formatting
    errors.py                   # domain exceptions -> HTTP handlers
    clock.py                    # Clock port (today()) — injectable for tests
  modules/
    profiles/                   # income, expenses, debts, assets, emergency fund, risk
      domain/      entities.py, value_objects.py
      application/ dto.py, ports.py, services.py
      infrastructure/ models.py, repository.py
      api/         router.py, schemas.py
    goals/                      # financial goals (target, deadline, priority)
      (same 4 layers)
    ingestion/                  # CSV summaries -> derived income/expense/debt per CIF
      domain/      entities.py
      application/ dto.py, ports.py, services.py
      infrastructure/ csv_source.py
      api/         router.py, schemas.py
    analysis/                   # THE ENGINE (pure formulas)
      domain/      formulas.py, thresholds.py, allocation.py, results.py
      application/ dto.py, services.py
      api/         router.py, schemas.py
    advisory/                   # purchase options, sub-scores, ranking, explanation
      domain/      options.py, subscores.py, fallback_scorer.py
      application/ dto.py, ports.py (RiskScorer), services.py
      api/         router.py, schemas.py
    explanation/                # RiskScorer adapters
      infrastructure/ bedrock_scorer.py, deterministic_scorer.py
      schemas.py   # strict JSON contract for the LLM output
alembic/                        # migrations
tests/
  unit/                         # golden-number tests from spec examples
  integration/                  # API tests against a test DB; Bedrock mocked
```

### 2.2 Module communication

Direct in-process use-case calls. `advisory` calls `analysis`; `analysis` reads
profile + goals via their repositories' read ports. No event bus (YAGNI).

### 2.3 Cross-cutting decisions

- **Money = `int` VNĐ** everywhere. Ratios, scores, months are floats. `money.py`
  centralizes conversion/rounding so currency never touches float arithmetic.
- **Async stack:** FastAPI + async SQLAlchemy 2.0 + asyncpg + Alembic.
- **Clock injection:** `Months_Remaining` is computed from the goal deadline vs.
  "today". A `Clock` port supplies `today()`; tests inject a fixed date so all
  time-dependent results are deterministic.
- **boto3 is sync:** the Bedrock adapter runs via `run_in_threadpool`.

## 3. Domain model

### 3.1 Profiles module

- **FinancialProfile** — root. Holds embedded income fields + emergency-fund
  balance; owns child collections.
  - Income: `salary` (required, ≥0), `secondary` (default 0), `avg_bonus_monthly`
    (= annual bonus / 12), `passive` (default 0). `total_income` = sum (computed).
- **Expense** (many) — `category`, `amount`, `classification ∈ {FIXED,
  SEMI_FIXED, DISCRETIONARY}`.
  - `total_expense` = sum of all. `essential_expense` = FIXED + SEMI_FIXED
    (excludes DISCRETIONARY) — used by EFR.
- **Debt** (many) — `name`, `monthly_payment` (required), `balance` (nullable for
  revolving), `apr`, `months_remaining` (nullable for revolving),
  `debt_type ∈ {REVOLVING, INSTALLMENT, SECURED}`.
  - `total_debt_payment` = sum of `monthly_payment`.
- **Asset** (many) — `type ∈ {CASH, SAVINGS, OTHER}`, `value`,
  `liquidity ∈ {HIGH, MEDIUM, LOW}`.
- **EmergencyFund** — `balance` (tracked separately from assets; never spent on
  installments).
- **RiskTolerance** — `LOW | MEDIUM | HIGH`.

### 3.2 Goals module

- **Goal** (many per profile) — `name`, `target_amount`, `deadline` (date),
  `priority ∈ {LOW, MEDIUM, HIGH, VERY_HIGH}`, `savings_allocated` (accumulated
  so far, default 0).
- `priority_weight`: VERY_HIGH=4, HIGH=3, MEDIUM=2, LOW=1.
- `months_remaining` = full months from `clock.today()` to `deadline` (computed,
  not stored).

## 4. The analysis engine (`analysis/domain/formulas.py`)

Each formula is a pure function. All take explicit inputs (no clock/DB reads).

| Function | Definition | Golden example |
|---|---|---|
| `net_cash_flow` | income − expense − debt_payment | 14,500,000 − 7,800,000 − 5,500,000 = **1,200,000** |
| `dti` | debt_payment / income × 100 | 5,500,000 / 14,500,000 = **37.93%** |
| `saving_rate` | (NCF − new_purchase_payment) / income × 100 | 1,200,000 / 14,500,000 = **8.28%** |
| `efr` | emergency_fund / essential_expense | 20,000,000 / 7,800,000 = **2.56** |
| `goal_gap` | target − savings_allocated | 300,000,000 − 0 = 300,000,000 |
| `gat` | goal_gap / monthly_saving_allocated | 300,000,000 / 400,000 = 750 |
| `goal_delay` | gat − months_remaining | 750 − 30 = 720 |
| `grs` | min(100, max(0, goal_delay / months_remaining × 100)) | min(100, 720/30×100) = **100** |
| `pgrs` | Σ(grs·weight) / Σ(weight) | (100·3 + 100·4 + 100·2)/9 = **100** |

### 4.1 Thresholds (`thresholds.py`)

- **DTI bands:** `<20` SAFE · `20–35` ACCEPTABLE · `35–40` WARNING · `>40` DANGER.
- **EFR safe threshold:** 3 months (recommended); benchmark in scoring uses 6/3/1.
- **Saving-rate recommendation:** ≥20%.

### 4.2 NCF allocation across goals (`allocation.py`)

GAT/GRS need a per-goal monthly allocation. Strategy is pluggable:

- `EvenAllocation` — split NCF equally (matches the spec's worked example).
- `PriorityWeightedAllocation` — split NCF by `priority_weight` ratio (**default**;
  the spec's special-case handling prefers this).

Golden tests use `EvenAllocation` to reproduce the doc's numbers exactly.

### 4.3 Edge cases (from the spec)

| Situation | Handling |
|---|---|
| NCF < 0 | All `grs = 100`; result flagged "reduce spending / raise income first". |
| `months_remaining ≤ 0` | `grs = 100`; result flags "overdue — delete, extend, or refund?". |
| `monthly_saving_allocated ≤ 0` | GAT = ∞ → `grs = 100` (goal unreachable at current allocation). |
| New goal added | All goals re-evaluated; response reports incremental delay. |

## 5. Advisory: options, sub-scores, scoring

### 5.1 Payment-option generation (`options.py`)

For a purchase amount `P` and an optional candidate-plan list (default:
pay-in-full, 3, 6, 12 months):

- Pay-in-full: one-time `P` (funded from cash/savings, not a monthly payment).
- Installment `n`: `monthly_payment = ceil(P / n)`; optional `apr` produces an
  amortized payment instead (default 0% → simple division).

### 5.2 Deterministic sub-scores (`subscores.py`) — engine, fed to the LLM

1. **S_CashFlow** — `100` if payment ≤ 50% NCF · `60` if 50–80% · `20` if
   80–100% · `0` if payment > NCF.
2. **S_Goal** — `100 − min(100, ΔPGRS × 3)` where `ΔPGRS = PGRS_new − PGRS_current`
   (continuous form is the source of truth; the doc's banded version is its
   approximation).
3. **S_EFR** — EFR after decision: `≥6 → 100` · `3–6 → 70` · `1–3 → 30` · `<1 → 0`.
   Emergency fund is never drawn down to pay installments.
4. **S_DTI** — `DTI_new = (debt_payment + new_payment) / income`:
   `<20 → 100` · `20–35 → 70` · `35–40 → 40` · `>40 → 0`.

### 5.3 Per-option metric packet

For each option the engine produces: `payment`, `ncf_new`, `dti_new`,
`efr_after`, `pgrs_new`, `delta_pgrs`, the 4 sub-scores, and hard-rule flags:

- `negative_cashflow` (NCF_new < 0): per the spec the system must warn and not
  recommend this option (it is still scored and shown with the warning).
- `requires_emergency_fund`: would force drawing the emergency fund → disallowed.

### 5.4 Risk scoring — LLM primary, deterministic fallback

`RiskScorer` is a port (`advisory/application/ports.py`) with two adapters:

- **`BedrockScorer`** (primary, `boto3`): sends the structured packet and asks for
  a strict JSON response. **Risk score convention: 0 = safest, 100 = riskiest.**
  Output schema (validated server-side):
  ```json
  {
    "options": [
      {"option_id": "str", "risk_score": 0-100, "recommended": true,
       "explanation": "str", "key_factors": ["str"]}
    ],
    "best_option_id": "str",
    "summary": "str"
  }
  ```
  On Bedrock error or schema-validation failure → automatic fallback.
- **`DeterministicScorer`** (fallback + tests): computes the weighted option score
  `0.35·S_CashFlow + 0.35·S_Goal + 0.20·S_EFR + 0.10·S_DTI`, then converts to
  risk: `risk_score = round(100 − weighted_score)`. Explanations are templated
  from the sub-scores and flags.

**Ranking:** ascending `risk_score` among options not blocked by a hard rule;
hard-rule-blocked options sort last and are marked not-recommended.

> **Assumption to confirm in review:** risk_score is "higher = riskier" and the
> winner is the lowest-risk allowed option. If you prefer "higher = better",
> we flip the convention in one place.

### 5.5 Note on the spec's example totals

The spec's worked "phone 15M" totals (48 / 36 / 55) do not reproduce from its own
weights, and no consistent weights produce all three. Per decision, the **LLM is
the scorer**; the weighted formula is only the deterministic fallback. We
golden-test the 4 sub-scores and the fallback formula — not the doc's totals.

## 6. Ingestion (CSV → profile)

- `csv_source.py` reads `summary_by_cif.csv` (whole-period) and
  `summary_by_cif_month.csv` (per month), reusing the existing classifier output.
- `POST /ingestion/import` loads a summary file into a staging table.
- Linking a profile to a CIF derives `total_income`, `total_expense`,
  `total_debt_payment` from the latest available month (or an average — config),
  which seed the profile. Manual entries always override derived values.

## 7. API surface

| Method | Path | Purpose |
|---|---|---|
| POST | `/profiles` | Create a profile (income, emergency fund, risk). |
| GET | `/profiles/{id}` | Fetch profile with children. |
| PUT/PATCH | `/profiles/{id}` | Update profile fields. |
| POST/PUT/DELETE | `/profiles/{id}/expenses` … `/debts` … `/assets` | Manage children. |
| POST/GET/PUT/DELETE | `/profiles/{id}/goals` | Manage goals. |
| POST | `/ingestion/import` | Load CSV summaries into staging. |
| GET | `/ingestion/cif/{cif}/summary` | Inspect a CIF's derived figures. |
| POST | `/profiles/{id}/link-cif` | Seed a profile from a CIF. |
| GET | `/profiles/{id}/analysis` | Current metrics (NCF, DTI, SR, EFR, per-goal GRS, PGRS). |
| POST | `/advisory/evaluate` | Evaluate a purchase → ranked options + metrics + explanation. |

**`POST /advisory/evaluate` request:** `{profile_id, item_name, purchase_amount,
candidate_plans?: [{type, months?, apr?}]}`.
**Response:** current metrics, per-option packet + risk_score + explanation,
`best_option_id`, `summary`, `scorer_used: "bedrock" | "deterministic"`.

## 8. Persistence (Postgres + async SQLAlchemy + Alembic)

Tables: `financial_profiles`, `expenses`, `debts`, `assets`, `goals`,
`cif_summaries` (ingestion staging). FKs indexed. Money columns are `BIGINT`
(VNĐ). Repositories implement the application-layer read/write ports; the domain
never imports SQLAlchemy.

## 9. Configuration (`core/config.py`, pydantic-settings)

`DATABASE_URL`, `DATABASE_URL_TEST`, `AWS_REGION`, `BEDROCK_MODEL_ID`,
`BEDROCK_ENABLED` (bool — off ⇒ always use deterministic scorer),
`ALLOCATION_STRATEGY` (`even|weighted`), scoring weights, EFR/DTI thresholds.
Secrets via env / `.env.local`; `.env.example` documents all keys. No secrets in
git.

## 10. Error handling

Domain exceptions (`ProfileNotFound`, `InvalidProfileData`, `GoalNotFound`,
`ScoringUnavailable`) map to HTTP codes in `core/errors.py`. Inputs validated at
the API boundary (Pydantic) and again in domain constructors (invariants like
`salary ≥ 0`). Internal errors return generic messages; details are logged.
Bedrock failures are caught and downgraded to the deterministic scorer, surfaced
via `scorer_used` rather than an error.

## 11. Testing

- **Unit (no I/O):** every formula against the spec's golden numbers (fixed clock,
  `EvenAllocation`); sub-score thresholds at every boundary; `DeterministicScorer`
  math; `money.py` rounding; allocation strategies.
- **Integration:** API endpoints against a test Postgres (`DATABASE_URL_TEST`,
  transactional rollback per test); Bedrock port mocked; one end-to-end
  `/advisory/evaluate` happy path + a negative-cashflow rejection path.
- **Bedrock adapter:** unit-tested with a stubbed boto3 client (valid JSON,
  malformed JSON → fallback, client error → fallback).

## 12. Tooling

`pyproject.toml`; `ruff` (lint/format); `mypy` strict (no `any`); `pytest` +
`pytest-asyncio`; `uvicorn`; `docker-compose.yml` for local Postgres;
`.env.example`; updated `README.md` with setup + run steps.

## 13. Out of scope (MVP)

Authentication/authorization, multi-user accounts, real banking integration,
front-end UI, scheduled re-confirmation reminders, debt-payoff-over-time
simulation (the spec's "dynamic GAT" combined projection). Interfaces are left
open so these can be added later.

## 14. Open assumptions (confirm in review)

1. Risk score convention: **higher = riskier** (winner = lowest risk). §5.4.
2. Default allocation strategy: **priority-weighted**; golden tests use even. §4.2.
3. CIF→profile seeding uses the **latest month** by default (config-switchable to
   average). §6.
4. Installment payment defaults to **simple `P/n`** (0% APR) unless `apr` given. §5.1.
