# BNPL Assistant

Personal-finance advisory MVP. A deterministic engine computes financial-health
metrics; an LLM (AWS Bedrock) assigns 0–100 risk scores to payment options, with
a deterministic fallback.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"                              # or: pip install -r requirements-dev.txt
cp .env.example .env
```

Dependencies are declared in `pyproject.toml`; equivalent pinned-floor
`requirements*.txt` files are provided for environments that don't install the
project as a package:

- `requirements.txt` — runtime deps
- `requirements-dev.txt` — runtime + test/lint tooling
- `requirements-forecast.txt` — adds optional Prophet (heavy Stan toolchain)

The cash-flow forecast works without Prophet via a built-in naive forecaster.

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

- `POST /auth/login` — exchange demo credentials for a bearer token (unprotected)
- `POST /profiles` — create a financial profile
- `GET /profiles/{id}/analysis` — NCF, DTI, saving rate, EFR, per-goal GRS, PGRS
- `POST /advisory/evaluate` — rank payment options for a purchase + explanation
- `GET /forecast/{cif}` — daily-net cash-flow history + Prophet forecast, next-30/90 net
- `GET /forecast/{cif}/chart.png` — rendered forecast chart (PNG)

All endpoints except `/auth/login` and `/health` require an
`Authorization: Bearer <token>` header when `AUTH_ENABLED=true`.

## Config (.env)

| Key | Default | Meaning |
|---|---|---|
| `PERSISTENCE` | `memory` | `memory` or `postgres` |
| `BEDROCK_ENABLED` | `false` | use Bedrock scorer; else deterministic |
| `ALLOCATION_STRATEGY` | `weighted` | `weighted` or `even` NCF split |
| `AUTH_ENABLED` | `true` | require a bearer token on protected endpoints |
| `AUTH_USERNAME` / `AUTH_PASSWORD` | `nguyenvana` / `123456` | demo login credentials |
| `AUTH_TOKEN` | `demo-token-bnpl` | bearer token returned by `/auth/login` |
| `TRANSACTIONS_CSV_PATH` | `transactions_labeled.csv` | source for cash-flow forecasting |
| `FORECAST_HORIZON_DAYS` | `90` | days to forecast ahead |
| `PROPHET_ENABLED` | `true` | use Prophet if installed; else naive forecaster |

## Frontend

A React + TypeScript SPA in `frontend/` that connects to the API.

```bash
# 1. start the backend (from repo root)
uvicorn app.main:app --reload    # serves on http://localhost:8000

# 2. start the frontend (from frontend/)
cd frontend
pnpm install
pnpm dev                          # serves on http://localhost:5173 (proxies /api -> :8000)
```

Open http://localhost:5173. Flow: **Nhập CIF** (optional, seeds the form from the
banking data) → **Hồ sơ** (create a profile) → **Phân tích** (metrics) →
**Đánh giá** (evaluate a purchase across payment options).

Frontend tests: `cd frontend && pnpm test`. Type-check: `pnpm exec tsc --noEmit`.

The ingestion screen needs `summary_by_cif_month.csv` present at the repo root
(produced by `transaction_classifier.py`) and `INGESTION_CSV_PATH` pointing to it.
