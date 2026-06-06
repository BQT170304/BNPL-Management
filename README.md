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
