# BNPL Assistant — Architecture

**Last updated:** 2026-06-07 (rev 2)
**Status:** Production (AWS ECS + S3 + CloudFront)

---

## Overview

BNPL Assistant is a personal finance advisory platform. Users create a financial profile (income, expenses, debts, goals), and the system:

1. Analyses financial health (NCF, DTI, EFR, PGRS scores)
2. Recommends and compares payment options (cash, instalment, credit card, BNPL)
3. Forecasts 30/90-day cash flow
4. Provides an AI copilot (LLM-backed) for free-form financial questions

---

## System Architecture

```
Browser (HTTPS)
    │
    ▼
CloudFront (d2ttyqgmp7bw35.cloudfront.net)
    ├── /* ──────────────→ S3 (bohu-frontend)    ← static HTML/JS/CSS
    └── /api/* ──────────→ ALB (port 80)
                               │
                               ▼
                         ECS Fargate (bnpl-backend)
                         private subnet, 2 vCPU / 4 GB
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
              RDS PostgreSQL        SSM Parameter Store
              (bohu, us-east-1)     DATABASE_URL
                                    LOCAL_LLM_AUTH
                                    OPENROUTER_API_KEY
                               │
                               ▼ (outbound HTTPS)
                         OpenRouter API
                         (qwen/qwen3-14b)
```

### VPC Topology

| Resource | Subnet type | Details |
|----------|-------------|---------|
| ALB | Public | `subnet-0e04561391eaabc1d`, `subnet-00e284c05f0952a56` |
| ECS tasks | Private | `subnet-0772e984ae088f691`, `subnet-0ff8998ccd68281e7` |
| RDS | Private | same private subnets |

**VPC Interface Endpoints** (all `available`): `ecr.dkr`, `ecr.api`, `logs`, `ssm`
**VPC Gateway Endpoint**: `s3`

Security group `sg-0a7250901e8ad525c` is shared by ECS tasks and VPC endpoint ENIs:
- Inbound 8000 from ALB SG (`sg-0d5d615243fbb2e13`)
- Inbound 443 self-referencing (so ECS tasks can reach VPC endpoints)

RDS security group `sg-004c9a91992cfc805`:
- Inbound 5432 from ECS SG (`sg-0a7250901e8ad525c`)

---

## Backend — Clean Architecture

```
FastAPI (app/)
  main.py              app factory, startup seed, DI wiring
  core/
    config.py          pydantic-settings (all config from env)
    database.py        async SQLAlchemy + session factory
  dependencies.py      singleton DI: repo, services, forecaster, auth
  modules/
    profiles/          financial profiles (CRUD, analysis triggers)
    goals/             savings goals
    analysis/          NCF / DTI / EFR / PGRS calculations
    advisory/          payment option scoring + simulation
    explanation/       deterministic scorer, OpenRouter scorer, local LLM scorer
    ml/                PD model scorer (sklearn, lazy-loaded)
    ingestion/         CIF CSV reader → profile seed
    forecasting/       naive forecaster (Prophet optional)
    consent/           user consent tracking
    decisions/         decision log + outcome recording
    feedback/          portfolio metrics + dataset export
    planning/          recommend + simulate endpoints
    copilot/           LLM chat (OpenRouter qwen/qwen3-14b)
    auth/              bearer token auth
    portfolio/         portfolio summary
alembic/               DB migrations
data/
  summary_by_cif_month.csv       CIF monthly aggregates
  transactions_labeled.csv       labelled transactions for ingestion
  demo_transactions_10001234.csv sample 18-month transaction history
```

Each module follows 4-layer clean architecture:
```
domain          entities, value objects — no I/O
application     use cases, ports (interfaces), DTOs
infrastructure  SQLAlchemy repos, CSV readers, HTTP adapters
api             FastAPI routers + Pydantic schemas
```

---

## Frontend — CDN-loaded React

The frontend (`frontend/public/`) uses in-browser Babel + React UMD — no build step required.

```
frontend/
  index.html          entry point; loads scripts in order
  public/
    config.js         window.API_BASE — injected empty ("") for CloudFront same-origin
    api.js            HTTP client (fetch + Bearer token + error handling)
    store.js          global state helpers
    ui.jsx            design system: Button, Card, Badge, LineChart, Icon, etc.
    tweaks-panel.jsx  dev tweaks overlay
    app.jsx           App root, LoginScreen, AppShell, logout
    user-screens-a/b/c.jsx   user-facing screens
    rm-screens.jsx    relationship manager screens
    styles.css        global styles (Inter + Geist Mono)
```

`window.API_BASE = ""` means all `/api/*` calls go to the same origin (CloudFront), which routes them to the ALB. No CORS issues.

---

## Key Environment Variables

| Variable | Where | Notes |
|----------|-------|-------|
| `DATABASE_URL` | SSM `/bnpl/prod/DATABASE_URL` | `postgresql+asyncpg://...` |
| `LOCAL_LLM_AUTH` | SSM `/bnpl/prod/LOCAL_LLM_AUTH` | Bearer token for local LLM |
| `OPENROUTER_API_KEY` | SSM `/bnpl/prod/OPENROUTER_API_KEY` | `sk-or-v1-...` |
| `PERSISTENCE` | ECS env | `postgres` |
| `AUTH_ENABLED` | ECS env | `true` |
| `AUTH_USERNAME` / `AUTH_PASSWORD` | ECS env | Login credentials |
| `AUTH_TOKEN` | ECS env | Static bearer token returned on login |
| `OPENROUTER_ENABLED` | ECS env | `true` |
| `OPENROUTER_MODEL` | ECS env | `qwen/qwen3-14b` |
| `LOCAL_LLM_ENABLED` | ECS env | `true` (takes priority over OpenRouter) |
| `LOCAL_LLM_URL` | ECS env | `http://203.113.152.4:7777/...` |
| `LOCAL_LLM_MODEL` | ECS env | `Qwen3-14B` |
| `BEDROCK_ENABLED` | ECS env | `false` (no IAM permission) |
| `FORECAST_ENGINE` | ECS env | `deterministic` |
| `ML_ENABLED` | ECS env | `true` (auto-disables if no model file) |
| `TRANSACTIONS_CSV_PATH` | ECS env | `data/transactions_labeled.csv` |

### LLM Scorer Priority Chain

```
LocalLLM (if LOCAL_LLM_ENABLED)
  → OpenRouter (if OPENROUTER_ENABLED + key present)
    → PD Model (if model file exists)
      → HardRules (always available, no LLM)
```

Each layer falls back to the next on timeout or error.

---

## CI/CD Pipeline

**Trigger:** push to `dev` branch  
**Workflow:** `.github/workflows/deploy.yml`

```
Job 1: deploy-backend
  1. Checkout
  2. OIDC → assume role GitHubActions-BNPL-Deploy
  3. ECR login
  4. docker build + push (tag = git SHA, ECR tags mutable)
  5. Render task definition with new image
  6. Create ECS service if missing / update if exists
  7. Wait for service stability

Job 2: deploy-frontend (needs: deploy-backend OR skipped)
  1. Checkout
  2. OIDC → assume role GitHubActions-BNPL-Deploy
  3. s3 sync frontend/public/ → s3://bohu-frontend/
  4. CloudFront invalidation E254OK1RKJMEXA /*
```

**IAM:** GitHub OIDC provider + `GitHubActions-BNPL-Deploy` role — no static AWS keys stored.

**Path-based triggers** — each job only runs when relevant files change:
- Backend: `app/**`, `alembic/**`, `Dockerfile`, `requirements*.txt`, `data/**`, `ecs-task-definition.json`
- Frontend: `frontend/**`
- `.github/**` changes alone trigger neither job

---

## AWS Resources

| Service | Name / ID | Notes |
|---------|-----------|-------|
| CloudFront | `E254OK1RKJMEXA` | `d2ttyqgmp7bw35.cloudfront.net` |
| S3 | `bohu-frontend` | static frontend, private + OAC |
| ALB | `bohu-alb-325198050.us-east-1.elb.amazonaws.com` | HTTP:80 → ECS:8000 |
| ECS Cluster | `bohu` | Fargate |
| ECS Service | `bnpl-backend-service` | desired 1, revision tracked by CI |
| ECR | `bnpl-backend` | mutable tags |
| RDS | `bohu` | PostgreSQL, private subnet |
| SSM | `/bnpl/prod/DATABASE_URL` `/bnpl/prod/LOCAL_LLM_AUTH` `/bnpl/prod/OPENROUTER_API_KEY` | SecureString |
| IAM Role (ECS) | `ecsTaskExecutionRole` | ECR pull + SSM secrets + CloudWatch logs |
| IAM Role (CI) | `GitHubActions-BNPL-Deploy` | OIDC, scoped to repo/dev branch |
