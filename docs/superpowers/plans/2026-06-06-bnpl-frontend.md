# BNPL Assistant Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A React + TypeScript SPA that connects to the FastAPI backend, with four screens (CIF import, profile builder, analysis dashboard, purchase evaluator), plus the backend ingestion HTTP API + CORS the frontend needs.

**Architecture:** Backend gains an ingestion router (wrapping the existing `CsvSummarySource` + `derive_seed`), CORS, and two config keys — additive, no domain changes. Frontend is a Vite SPA: a typed `fetch` client + endpoints, pure helpers (money/bands/form-mapping), a generic async hook, a small UI kit, and four feature screens wired by an `activeProfileId` context.

**Tech Stack:** Backend: FastAPI (existing), pytest. Frontend: React 18, TypeScript strict, Vite, Tailwind CSS, Vitest + React Testing Library, pnpm.

**Reference spec:** `docs/superpowers/specs/2026-06-06-bnpl-frontend-design.md`

**Backend conventions:** Python money is `int` VND; domain imports no framework; run `ruff check app && mypy app && pytest -q` before backend commits.

**Frontend conventions:** TypeScript strict, no `any`. Run `pnpm test` (and `pnpm exec tsc --noEmit`) before frontend commits. Work in `frontend/`.

---

# PART 1 — BACKEND ADDITIONS

## Task 1: Config keys + CifNotFound error

**Files:**
- Modify: `app/core/config.py`
- Modify: `app/core/errors.py`
- Test: `tests/unit/test_config.py` (add a test)

- [ ] **Step 1: Write the failing test** (append to `tests/unit/test_config.py`)

```python
def test_ingestion_and_cors_defaults():
    s = Settings(_env_file=None)
    assert s.ingestion_csv_path == "summary_by_cif_month.csv"
    assert s.cors_origins == "http://localhost:5173"
    assert s.cors_origin_list == ["http://localhost:5173"]
```

- [ ] **Step 2: Run it — expect FAIL**

Run: `python -m pytest tests/unit/test_config.py::test_ingestion_and_cors_defaults -v`
Expected: FAIL (AttributeError: ingestion_csv_path).

- [ ] **Step 3: Add the settings** — in `app/core/config.py`, inside `Settings`, after the `efr_safe_months` line add:

```python
    ingestion_csv_path: str = "summary_by_cif_month.csv"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]
```

- [ ] **Step 4: Add the error** — in `app/core/errors.py` add:

```python
class CifNotFound(DomainError):
    def __init__(self, cif: str) -> None:
        super().__init__(f"CIF not found: {cif}")
        self.cif = cif
```

- [ ] **Step 5: Run — expect PASS**

Run: `python -m pytest tests/unit/test_config.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/core/config.py app/core/errors.py tests/unit/test_config.py
git commit -m "feat(core): add ingestion/cors config and CifNotFound error"
```

---

## Task 2: IngestionService (list CIFs, get seed)

**Files:**
- Create: `app/modules/ingestion/application/service.py`
- Test: `tests/unit/test_ingestion_service.py`

The existing `app/modules/ingestion/application/ports.py` defines `CifSummary` and the
`SummarySource` Protocol; `services.py` defines `CifSeed` and `derive_seed`. This task
adds a stateful service that caches loaded summaries and exposes list/seed.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_ingestion_service.py
import pytest

from app.core.errors import CifNotFound
from app.modules.ingestion.application.ports import CifSummary
from app.modules.ingestion.application.service import IngestionService


class _StubSource:
    def __init__(self, rows: list[CifSummary]):
        self._rows = rows
        self.load_calls = 0

    def load(self, path: str) -> list[CifSummary]:
        self.load_calls += 1
        return self._rows


def _rows() -> list[CifSummary]:
    return [
        CifSummary("100", "2025-01", 10_000_000, 4_000_000, 1_000_000),
        CifSummary("100", "2025-02", 12_000_000, 5_000_000, 2_000_000),
        CifSummary("200", "2025-01", 20_000_000, 8_000_000, 3_000_000),
    ]


def test_list_cifs_returns_sorted_distinct():
    svc = IngestionService(_StubSource(_rows()), csv_path="x.csv")
    assert svc.list_cifs() == ["100", "200"]


def test_get_seed_latest():
    svc = IngestionService(_StubSource(_rows()), csv_path="x.csv")
    seed = svc.get_seed("100", strategy="latest")
    assert (seed.income, seed.expense, seed.debt_payment) == (12_000_000, 5_000_000, 2_000_000)


def test_get_seed_unknown_cif_raises_cifnotfound():
    svc = IngestionService(_StubSource(_rows()), csv_path="x.csv")
    with pytest.raises(CifNotFound):
        svc.get_seed("999")


def test_summaries_loaded_once_and_cached():
    source = _StubSource(_rows())
    svc = IngestionService(source, csv_path="x.csv")
    svc.list_cifs()
    svc.get_seed("100")
    assert source.load_calls == 1
```

- [ ] **Step 2: Run — expect FAIL**

Run: `python -m pytest tests/unit/test_ingestion_service.py -v`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement**

```python
# app/modules/ingestion/application/service.py
from __future__ import annotations

from app.core.errors import CifNotFound
from app.modules.ingestion.application.ports import CifSummary, SummarySource
from app.modules.ingestion.application.services import CifSeed, derive_seed


class IngestionService:
    """Loads the summary CSV once and serves CIF lists and derived seeds."""

    def __init__(self, source: SummarySource, csv_path: str) -> None:
        self._source = source
        self._csv_path = csv_path
        self._rows: list[CifSummary] | None = None

    def _summaries(self) -> list[CifSummary]:
        if self._rows is None:
            self._rows = self._source.load(self._csv_path)
        return self._rows

    def list_cifs(self) -> list[str]:
        return sorted({r.cif for r in self._summaries()})

    def get_seed(self, cif: str, strategy: str = "latest") -> CifSeed:
        rows = self._summaries()
        if not any(r.cif == cif for r in rows):
            raise CifNotFound(cif)
        return derive_seed(cif, rows, strategy=strategy)
```

- [ ] **Step 4: Run — expect PASS**

Run: `python -m pytest tests/unit/test_ingestion_service.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add app/modules/ingestion/application/service.py tests/unit/test_ingestion_service.py
git commit -m "feat(ingestion): add IngestionService with cached CSV load"
```

---

## Task 3: Ingestion router + CORS + DI wiring

**Files:**
- Create: `app/modules/ingestion/api/__init__.py`, `app/modules/ingestion/api/schemas.py`, `app/modules/ingestion/api/router.py`
- Modify: `app/dependencies.py`, `app/main.py`
- Test: `tests/integration/test_ingestion_api.py`

- [ ] **Step 1: Write the failing integration test**

```python
# tests/integration/test_ingestion_api.py
import pytest
from httpx import ASGITransport, AsyncClient

import app.dependencies as deps
from app.main import create_app
from app.modules.ingestion.application.ports import CifSummary
from app.modules.ingestion.application.service import IngestionService


class _StubSource:
    def load(self, path: str) -> list[CifSummary]:
        return [
            CifSummary("100", "2025-01", 10_000_000, 4_000_000, 1_000_000),
            CifSummary("100", "2025-02", 12_000_000, 5_000_000, 2_000_000),
        ]


@pytest.fixture
async def client(monkeypatch):
    svc = IngestionService(_StubSource(), csv_path="x.csv")
    monkeypatch.setattr(deps, "get_ingestion_service", lambda: svc)
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_list_cifs(client):
    r = await client.get("/ingestion/cifs")
    assert r.status_code == 200
    assert r.json() == {"cifs": ["100"]}


async def test_get_seed_latest(client):
    r = await client.get("/ingestion/cif/100/seed?strategy=latest")
    assert r.status_code == 200
    assert r.json() == {"cif": "100", "income": 12_000_000,
                        "expense": 5_000_000, "debt_payment": 2_000_000}


async def test_get_seed_unknown_cif_404(client):
    r = await client.get("/ingestion/cif/999/seed")
    assert r.status_code == 404
```

> Note: the router resolves the service via `Depends(deps.get_ingestion_service)`.
> Because the test monkeypatches `deps.get_ingestion_service`, the router MUST
> reference it as `deps.get_ingestion_service` (module attribute), not import the
> function by name. See Step 3.

- [ ] **Step 2: Run — expect FAIL**

Run: `python -m pytest tests/integration/test_ingestion_api.py -v`
Expected: FAIL (404 for all — routes not registered).

- [ ] **Step 3: Implement the schemas + router**

```python
# app/modules/ingestion/api/schemas.py
from __future__ import annotations

from pydantic import BaseModel


class CifsOut(BaseModel):
    cifs: list[str]


class CifSeedOut(BaseModel):
    cif: str
    income: int
    expense: int
    debt_payment: int
```

```python
# app/modules/ingestion/api/router.py
from __future__ import annotations

from fastapi import APIRouter, Depends

import app.dependencies as deps
from app.modules.ingestion.api.schemas import CifSeedOut, CifsOut
from app.modules.ingestion.application.service import IngestionService

router = APIRouter(tags=["ingestion"])


def _service() -> IngestionService:
    # Indirection so tests can monkeypatch deps.get_ingestion_service.
    return deps.get_ingestion_service()


@router.get("/ingestion/cifs", response_model=CifsOut)
async def list_cifs(service: IngestionService = Depends(_service)) -> CifsOut:
    return CifsOut(cifs=service.list_cifs())


@router.get("/ingestion/cif/{cif}/seed", response_model=CifSeedOut)
async def get_seed(
    cif: str, strategy: str = "latest",
    service: IngestionService = Depends(_service),
) -> CifSeedOut:
    seed = service.get_seed(cif, strategy=strategy)
    return CifSeedOut(cif=seed.cif, income=seed.income,
                      expense=seed.expense, debt_payment=seed.debt_payment)
```

- [ ] **Step 4: Wire DI** — in `app/dependencies.py` add near the other getters:

```python
from app.core.config import get_settings
from app.modules.ingestion.application.service import IngestionService
from app.modules.ingestion.infrastructure.csv_source import CsvSummarySource

_ingestion_service: IngestionService | None = None


def get_ingestion_service() -> IngestionService:
    global _ingestion_service
    if _ingestion_service is None:
        s = get_settings()
        _ingestion_service = IngestionService(CsvSummarySource(), s.ingestion_csv_path)
    return _ingestion_service
```

(If `get_settings` is already imported in `dependencies.py`, don't duplicate the import.)

- [ ] **Step 5: Wire router + CORS + error handler** — in `app/main.py`:

Add imports at the top:

```python
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import CifNotFound
from app.modules.ingestion.api.router import router as ingestion_router
```

Inside `create_app()`, after the existing `app.include_router(...)` calls add:

```python
    app.include_router(ingestion_router)
```

After creating `app = FastAPI(...)` (before returning), add the middleware:

```python
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

Add `CifNotFound` to the 404 handler — change the existing stacked decorator block so `CifNotFound` is also handled as 404:

```python
    @app.exception_handler(ProfileNotFound)
    @app.exception_handler(GoalNotFound)
    @app.exception_handler(CifNotFound)
    async def not_found(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})
```

- [ ] **Step 6: Run — expect PASS, then full suite**

Run: `python -m pytest tests/integration/test_ingestion_api.py -v`
Expected: PASS (3 tests).
Run: `ruff check app && mypy app && python -m pytest -q`
Expected: clean; all green (Postgres test still skips).

- [ ] **Step 7: Commit**

```bash
git add app/modules/ingestion/api app/dependencies.py app/main.py tests/integration/test_ingestion_api.py
git commit -m "feat(ingestion): add ingestion HTTP API and CORS"
```

---

# PART 2 — FRONTEND

## Task 4: Scaffold the Vite React+TS+Tailwind project

**Files:**
- Create: `frontend/package.json`, `frontend/tsconfig.json`, `frontend/tsconfig.node.json`, `frontend/vite.config.ts`, `frontend/vitest.config.ts`, `frontend/tailwind.config.js`, `frontend/postcss.config.js`, `frontend/index.html`, `frontend/.gitignore`, `frontend/src/index.css`, `frontend/src/test/setup.ts`

- [ ] **Step 1: Create `frontend/package.json`**

```json
{
  "name": "bnpl-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc --noEmit && vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:watch": "vitest",
    "lint": "tsc --noEmit"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.4.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/user-event": "^14.5.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "autoprefixer": "^10.4.0",
    "jsdom": "^24.1.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.5.0",
    "vite": "^5.4.0",
    "vitest": "^2.0.0"
  }
}
```

- [ ] **Step 2: Create the config files**

`frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "types": ["vitest/globals", "@testing-library/jest-dom"]
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

`frontend/tsconfig.node.json`:

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true,
    "strict": true
  },
  "include": ["vite.config.ts", "vitest.config.ts"]
}
```

`frontend/vite.config.ts`:

```ts
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
```

`frontend/vitest.config.ts`:

```ts
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
  },
});
```

`frontend/tailwind.config.js`:

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: { extend: {} },
  plugins: [],
};
```

`frontend/postcss.config.js`:

```js
export default {
  plugins: { tailwindcss: {}, autoprefixer: {} },
};
```

`frontend/.gitignore`:

```
node_modules/
dist/
*.local
```

- [ ] **Step 3: Create the HTML + CSS + test setup**

`frontend/index.html`:

```html
<!doctype html>
<html lang="vi">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>BNPL Assistant</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

`frontend/src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  @apply bg-slate-50 text-slate-800;
}
```

`frontend/src/test/setup.ts`:

```ts
import "@testing-library/jest-dom/vitest";
```

- [ ] **Step 4: Install and verify**

Run (in `frontend/`): `pnpm install`
Expected: installs without error.
Run: `pnpm exec tsc --noEmit`
Expected: passes (no source files yet beyond configs → no errors).

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/pnpm-lock.yaml frontend/tsconfig.json frontend/tsconfig.node.json frontend/vite.config.ts frontend/vitest.config.ts frontend/tailwind.config.js frontend/postcss.config.js frontend/index.html frontend/.gitignore frontend/src/index.css frontend/src/test/setup.ts
git commit -m "chore(frontend): scaffold Vite React+TS+Tailwind project"
```

---

## Task 5: API types

**Files:**
- Create: `frontend/src/api/types.ts`

These mirror the backend Pydantic schemas exactly. No test (types only); they are
exercised by later tasks.

- [ ] **Step 1: Create `frontend/src/api/types.ts`**

```ts
export type Classification = "FIXED" | "SEMI_FIXED" | "DISCRETIONARY";
export type DebtType = "REVOLVING" | "INSTALLMENT" | "SECURED";
export type AssetType = "CASH" | "SAVINGS" | "OTHER";
export type Liquidity = "HIGH" | "MEDIUM" | "LOW";
export type Risk = "LOW" | "MEDIUM" | "HIGH";
export type Priority = "LOW" | "MEDIUM" | "HIGH" | "VERY_HIGH";
export type DtiBand = "SAFE" | "ACCEPTABLE" | "WARNING" | "DANGER";

export interface IncomeIn {
  salary: number;
  secondary: number;
  avg_bonus_monthly: number;
  passive: number;
}
export interface ExpenseIn {
  category: string;
  amount: number;
  classification: Classification;
}
export interface DebtIn {
  name: string;
  monthly_payment: number;
  balance: number | null;
  apr: number;
  months_remaining: number | null;
  debt_type: DebtType;
}
export interface AssetIn {
  type: AssetType;
  value: number;
  liquidity: Liquidity;
}
export interface GoalIn {
  id: string;
  name: string;
  target_amount: number;
  deadline: string; // YYYY-MM-DD
  priority: Priority;
  savings_allocated: number;
}
export interface ProfileIn {
  id: string;
  income: IncomeIn;
  risk: Risk;
  emergency_fund: number;
  expenses: ExpenseIn[];
  debts: DebtIn[];
  assets: AssetIn[];
  goals: GoalIn[];
}

export interface GoalMetricOut {
  goal_id: string;
  name: string;
  gap: number;
  monthly_allocated: number;
  gat: number;
  delay: number;
  grs: number;
  months_remaining: number;
}
export interface MetricsOut {
  ncf: number;
  dti: number;
  dti_band: DtiBand;
  saving_rate: number;
  efr: number;
  pgrs: number;
  goals: GoalMetricOut[];
  flags: string[];
}

export interface PlanIn {
  type: "PAY_IN_FULL" | "INSTALLMENT";
  months: number | null;
  apr: number;
}
export interface EvaluateIn {
  profile_id: string;
  item_name: string;
  purchase_amount: number;
  candidate_plans: PlanIn[] | null;
}
export interface OptionScoreOut {
  option_id: string;
  risk_score: number;
  recommended: boolean;
  explanation: string;
  key_factors: string[];
  monthly_payment: number;
  ncf_new: number;
  dti_new: number;
  efr_after: number;
  delta_pgrs: number;
  flags: string[];
}
export interface EvaluateOut {
  best_option_id: string;
  summary: string;
  scorer_used: string;
  options: OptionScoreOut[];
}

export interface CifSeed {
  cif: string;
  income: number;
  expense: number;
  debt_payment: number;
}
```

- [ ] **Step 2: Verify it compiles**

Run (in `frontend/`): `pnpm exec tsc --noEmit`
Expected: passes.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/types.ts
git commit -m "feat(frontend): add API types mirroring backend schemas"
```

---

## Task 6: API client (typed fetch + ApiError)

**Files:**
- Create: `frontend/src/api/client.ts`
- Test: `frontend/src/api/client.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// frontend/src/api/client.test.ts
import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch } from "./client";

afterEach(() => vi.restoreAllMocks());

function mockFetch(status: number, body: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () =>
      new Response(JSON.stringify(body), {
        status,
        headers: { "Content-Type": "application/json" },
      }),
    ),
  );
}

describe("apiFetch", () => {
  it("returns parsed JSON on 200", async () => {
    mockFetch(200, { id: "p1" });
    const data = await apiFetch<{ id: string }>("/profiles");
    expect(data).toEqual({ id: "p1" });
  });

  it("prefixes /api and passes method/body", async () => {
    const spy = vi.fn(async () => new Response("{}", { status: 200 }));
    vi.stubGlobal("fetch", spy);
    await apiFetch("/profiles", { method: "POST", body: JSON.stringify({ a: 1 }) });
    expect(spy).toHaveBeenCalledWith(
      "/api/profiles",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("throws ApiError with detail on non-2xx", async () => {
    mockFetch(404, { detail: "Profile not found: p1" });
    await expect(apiFetch("/profiles/p1/analysis")).rejects.toMatchObject({
      status: 404,
      detail: "Profile not found: p1",
    });
  });

  it("ApiError is an Error", async () => {
    const err = new ApiError(400, "bad");
    expect(err).toBeInstanceOf(Error);
    expect(err.message).toContain("bad");
  });
});
```

- [ ] **Step 2: Run — expect FAIL**

Run (in `frontend/`): `pnpm test -- client`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement**

```ts
// frontend/src/api/client.ts
const BASE = "/api";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
  } catch {
    throw new ApiError(0, "Không kết nối được máy chủ");
  }

  const text = await response.text();
  const data: unknown = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const detail =
      data && typeof data === "object" && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : `Lỗi máy chủ (${response.status})`;
    throw new ApiError(response.status, detail);
  }
  return data as T;
}
```

- [ ] **Step 4: Run — expect PASS**

Run (in `frontend/`): `pnpm test -- client`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/client.ts frontend/src/api/client.test.ts
git commit -m "feat(frontend): add typed fetch client with ApiError"
```

---

## Task 7: API endpoints

**Files:**
- Create: `frontend/src/api/endpoints.ts`

- [ ] **Step 1: Create `frontend/src/api/endpoints.ts`**

```ts
import { apiFetch } from "./client";
import type { CifSeed, EvaluateIn, EvaluateOut, MetricsOut, ProfileIn } from "./types";

export function createProfile(body: ProfileIn): Promise<{ id: string }> {
  return apiFetch<{ id: string }>("/profiles", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getAnalysis(profileId: string): Promise<MetricsOut> {
  return apiFetch<MetricsOut>(`/profiles/${profileId}/analysis`);
}

export function evaluatePurchase(body: EvaluateIn): Promise<EvaluateOut> {
  return apiFetch<EvaluateOut>("/advisory/evaluate", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function listCifs(): Promise<string[]> {
  return apiFetch<{ cifs: string[] }>("/ingestion/cifs").then((r) => r.cifs);
}

export function getCifSeed(cif: string, strategy: "latest" | "average"): Promise<CifSeed> {
  return apiFetch<CifSeed>(`/ingestion/cif/${cif}/seed?strategy=${strategy}`);
}
```

- [ ] **Step 2: Verify compile**

Run (in `frontend/`): `pnpm exec tsc --noEmit`
Expected: passes.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/endpoints.ts
git commit -m "feat(frontend): add typed API endpoint functions"
```

---

## Task 8: money + bands helpers

**Files:**
- Create: `frontend/src/lib/money.ts`, `frontend/src/lib/bands.ts`
- Test: `frontend/src/lib/money.test.ts`, `frontend/src/lib/bands.test.ts`

- [ ] **Step 1: Write the failing tests**

```ts
// frontend/src/lib/money.test.ts
import { describe, expect, it } from "vitest";
import { formatVnd, parseVnd } from "./money";

describe("money", () => {
  it("formats with dot separators and ₫", () => {
    expect(formatVnd(14_500_000)).toBe("14.500.000 ₫");
    expect(formatVnd(0)).toBe("0 ₫");
    expect(formatVnd(-800_000)).toBe("-800.000 ₫");
  });
  it("parses digit strings (ignoring separators) to int", () => {
    expect(parseVnd("14.500.000")).toBe(14_500_000);
    expect(parseVnd("14,500,000 ₫")).toBe(14_500_000);
    expect(parseVnd("")).toBe(0);
    expect(parseVnd("abc")).toBe(0);
  });
});
```

```ts
// frontend/src/lib/bands.test.ts
import { describe, expect, it } from "vitest";
import { dtiBandClass, riskClass } from "./bands";

describe("bands", () => {
  it("maps DTI bands to color classes", () => {
    expect(dtiBandClass("SAFE")).toContain("green");
    expect(dtiBandClass("ACCEPTABLE")).toContain("blue");
    expect(dtiBandClass("WARNING")).toContain("amber");
    expect(dtiBandClass("DANGER")).toContain("red");
  });
  it("maps risk score to color classes by quartile", () => {
    expect(riskClass(10)).toContain("green");
    expect(riskClass(40)).toContain("blue");
    expect(riskClass(70)).toContain("amber");
    expect(riskClass(90)).toContain("red");
  });
});
```

- [ ] **Step 2: Run — expect FAIL**

Run (in `frontend/`): `pnpm test -- lib`
Expected: FAIL (modules not found).

- [ ] **Step 3: Implement**

```ts
// frontend/src/lib/money.ts
export function formatVnd(amount: number): string {
  const sign = amount < 0 ? "-" : "";
  const digits = Math.abs(Math.round(amount)).toString();
  const grouped = digits.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `${sign}${grouped} ₫`;
}

export function parseVnd(input: string): number {
  const digits = input.replace(/[^\d]/g, "");
  return digits ? Number.parseInt(digits, 10) : 0;
}
```

```ts
// frontend/src/lib/bands.ts
import type { DtiBand } from "../api/types";

const BADGE = "px-2 py-0.5 rounded-full text-xs font-medium";

export function dtiBandClass(band: DtiBand): string {
  const map: Record<DtiBand, string> = {
    SAFE: "bg-green-100 text-green-800",
    ACCEPTABLE: "bg-blue-100 text-blue-800",
    WARNING: "bg-amber-100 text-amber-800",
    DANGER: "bg-red-100 text-red-800",
  };
  return `${BADGE} ${map[band]}`;
}

export function riskClass(score: number): string {
  if (score <= 25) return `${BADGE} bg-green-100 text-green-800`;
  if (score <= 50) return `${BADGE} bg-blue-100 text-blue-800`;
  if (score <= 75) return `${BADGE} bg-amber-100 text-amber-800`;
  return `${BADGE} bg-red-100 text-red-800`;
}
```

- [ ] **Step 4: Run — expect PASS**

Run (in `frontend/`): `pnpm test -- lib`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib
git commit -m "feat(frontend): add money formatting and band color helpers"
```

---

## Task 9: useAsync hook

**Files:**
- Create: `frontend/src/hooks/useAsync.ts`
- Test: `frontend/src/hooks/useAsync.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/src/hooks/useAsync.test.tsx
import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ApiError } from "../api/client";
import { useAsync } from "./useAsync";

describe("useAsync", () => {
  it("sets data on success", async () => {
    const { result } = renderHook(() => useAsync(async (n: number) => n * 2));
    await act(async () => {
      await result.current.run(21);
    });
    expect(result.current.data).toBe(42);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("captures ApiError message", async () => {
    const { result } = renderHook(() =>
      useAsync(async () => {
        throw new ApiError(404, "nope");
      }),
    );
    await act(async () => {
      await result.current.run().catch(() => undefined);
    });
    await waitFor(() => expect(result.current.error).toBe("nope"));
  });
});
```

- [ ] **Step 2: Run — expect FAIL**

Run (in `frontend/`): `pnpm test -- useAsync`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement**

```ts
// frontend/src/hooks/useAsync.ts
import { useCallback, useState } from "react";
import { ApiError } from "../api/client";

interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export function useAsync<TArgs extends unknown[], TData>(
  fn: (...args: TArgs) => Promise<TData>,
) {
  const [state, setState] = useState<AsyncState<TData>>({
    data: null,
    loading: false,
    error: null,
  });

  const run = useCallback(
    async (...args: TArgs): Promise<TData> => {
      setState((s) => ({ ...s, loading: true, error: null }));
      try {
        const data = await fn(...args);
        setState({ data, loading: false, error: null });
        return data;
      } catch (err) {
        const message =
          err instanceof ApiError ? err.detail : "Đã xảy ra lỗi không xác định";
        setState((s) => ({ ...s, loading: false, error: message }));
        throw err;
      }
    },
    [fn],
  );

  return { ...state, run };
}
```

- [ ] **Step 4: Run — expect PASS**

Run (in `frontend/`): `pnpm test -- useAsync`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/hooks
git commit -m "feat(frontend): add useAsync hook"
```

---

## Task 10: UI kit

**Files:**
- Create: `frontend/src/components/ui/Card.tsx`, `Button.tsx`, `Badge.tsx`, `Field.tsx`, `TextInput.tsx`, `NumberInput.tsx`, `Select.tsx`, `Spinner.tsx`, `ErrorBanner.tsx`, `Metric.tsx`

Small presentational components. No tests (covered indirectly by feature tests).

- [ ] **Step 1: Create the components**

`frontend/src/components/ui/Card.tsx`:

```tsx
import type { ReactNode } from "react";

export function Card({ title, children }: { title?: string; children: ReactNode }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      {title && <h3 className="mb-3 text-sm font-semibold text-slate-500">{title}</h3>}
      {children}
    </div>
  );
}
```

`frontend/src/components/ui/Button.tsx`:

```tsx
import type { ButtonHTMLAttributes } from "react";

export function Button({
  variant = "primary",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "ghost" }) {
  const base =
    "inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50";
  const styles =
    variant === "primary"
      ? "bg-indigo-600 text-white hover:bg-indigo-700"
      : "bg-slate-100 text-slate-700 hover:bg-slate-200";
  return <button className={`${base} ${styles} ${className}`} {...props} />;
}
```

`frontend/src/components/ui/Badge.tsx`:

```tsx
export function Badge({ className, children }: { className: string; children: React.ReactNode }) {
  return <span className={className}>{children}</span>;
}
```

`frontend/src/components/ui/Field.tsx`:

```tsx
import type { ReactNode } from "react";

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-slate-600">{label}</span>
      {children}
    </label>
  );
}
```

`frontend/src/components/ui/TextInput.tsx`:

```tsx
import type { InputHTMLAttributes } from "react";

export function TextInput(props: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      type="text"
      {...props}
      className={`w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none ${props.className ?? ""}`}
    />
  );
}
```

`frontend/src/components/ui/NumberInput.tsx`:

```tsx
import { parseVnd, formatVnd } from "../../lib/money";

export function NumberInput({
  value,
  onValueChange,
  ariaLabel,
}: {
  value: number;
  onValueChange: (v: number) => void;
  ariaLabel?: string;
}) {
  return (
    <input
      type="text"
      inputMode="numeric"
      aria-label={ariaLabel}
      value={value === 0 ? "" : formatVnd(value).replace(" ₫", "")}
      onChange={(e) => onValueChange(parseVnd(e.target.value))}
      placeholder="0"
      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
    />
  );
}
```

`frontend/src/components/ui/Select.tsx`:

```tsx
import type { SelectHTMLAttributes } from "react";

export function Select({
  options,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement> & { options: { value: string; label: string }[] }) {
  return (
    <select
      {...props}
      className={`w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none ${props.className ?? ""}`}
    >
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  );
}
```

`frontend/src/components/ui/Spinner.tsx`:

```tsx
export function Spinner() {
  return <div role="status" className="text-sm text-slate-500">Đang tải…</div>;
}
```

`frontend/src/components/ui/ErrorBanner.tsx`:

```tsx
export function ErrorBanner({ message }: { message: string }) {
  return (
    <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {message}
    </div>
  );
}
```

`frontend/src/components/ui/Metric.tsx`:

```tsx
import type { ReactNode } from "react";

export function Metric({ label, value, hint }: { label: string; value: ReactNode; hint?: ReactNode }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="text-xs font-medium text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-slate-800">{value}</div>
      {hint && <div className="mt-1 text-xs text-slate-400">{hint}</div>}
    </div>
  );
}
```

- [ ] **Step 2: Verify compile**

Run (in `frontend/`): `pnpm exec tsc --noEmit`
Expected: passes.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ui
git commit -m "feat(frontend): add UI kit components"
```

---

## Task 11: activeProfile context

**Files:**
- Create: `frontend/src/state/activeProfile.tsx`

- [ ] **Step 1: Create `frontend/src/state/activeProfile.tsx`**

```tsx
import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

const KEY = "bnpl.activeProfileId";

interface Ctx {
  activeProfileId: string | null;
  setActiveProfileId: (id: string) => void;
}

const ActiveProfileContext = createContext<Ctx | null>(null);

export function ActiveProfileProvider({ children }: { children: ReactNode }) {
  const [activeProfileId, setId] = useState<string | null>(
    () => localStorage.getItem(KEY),
  );
  const setActiveProfileId = useCallback((id: string) => {
    localStorage.setItem(KEY, id);
    setId(id);
  }, []);
  return (
    <ActiveProfileContext.Provider value={{ activeProfileId, setActiveProfileId }}>
      {children}
    </ActiveProfileContext.Provider>
  );
}

export function useActiveProfile(): Ctx {
  const ctx = useContext(ActiveProfileContext);
  if (!ctx) throw new Error("useActiveProfile must be used within ActiveProfileProvider");
  return ctx;
}
```

- [ ] **Step 2: Verify compile**

Run (in `frontend/`): `pnpm exec tsc --noEmit`
Expected: passes.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/state
git commit -m "feat(frontend): add activeProfile context"
```

---

## Task 12: profile form model (pure mapping)

**Files:**
- Create: `frontend/src/features/profile/profileForm.ts`
- Test: `frontend/src/features/profile/profileForm.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// frontend/src/features/profile/profileForm.test.ts
import { describe, expect, it } from "vitest";
import { emptyForm, seedToForm, toProfileIn } from "./profileForm";

describe("profileForm", () => {
  it("emptyForm has a generated id and empty lists", () => {
    const f = emptyForm();
    expect(f.id).toMatch(/^p-/);
    expect(f.expenses).toEqual([]);
    expect(f.goals).toEqual([]);
  });

  it("toProfileIn builds the API body with numeric values", () => {
    const f = emptyForm();
    f.income.salary = 10_000_000;
    f.emergency_fund = 20_000_000;
    f.risk = "MEDIUM";
    f.expenses = [{ category: "rent", amount: 3_000_000, classification: "FIXED" }];
    f.goals = [
      { name: "Car", target_amount: 300_000_000, deadline: "2027-12-01",
        priority: "HIGH", savings_allocated: 0 },
    ];
    const body = toProfileIn(f);
    expect(body.id).toBe(f.id);
    expect(body.income.salary).toBe(10_000_000);
    expect(body.expenses[0].classification).toBe("FIXED");
    expect(body.goals[0].id).toMatch(/^g-/); // goal id generated
    expect(body.goals[0].target_amount).toBe(300_000_000);
  });

  it("seedToForm fills aggregate income/expense/debt", () => {
    const f = seedToForm({ cif: "100", income: 12_000_000, expense: 5_000_000, debt_payment: 2_000_000 });
    expect(f.income.salary).toBe(12_000_000);
    expect(f.expenses).toHaveLength(1);
    expect(f.expenses[0].amount).toBe(5_000_000);
    expect(f.expenses[0].classification).toBe("SEMI_FIXED");
    expect(f.debts).toHaveLength(1);
    expect(f.debts[0].monthly_payment).toBe(2_000_000);
  });
});
```

- [ ] **Step 2: Run — expect FAIL**

Run (in `frontend/`): `pnpm test -- profileForm`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement**

```ts
// frontend/src/features/profile/profileForm.ts
import type {
  AssetIn, Classification, DebtIn, ExpenseIn, IncomeIn,
  ProfileIn, Risk,
} from "../../api/types";
import type { CifSeed } from "../../api/types";

export interface GoalFormRow {
  name: string;
  target_amount: number;
  deadline: string;
  priority: ProfileIn["goals"][number]["priority"];
  savings_allocated: number;
}

export interface ProfileFormState {
  id: string;
  income: IncomeIn;
  risk: Risk;
  emergency_fund: number;
  expenses: ExpenseIn[];
  debts: DebtIn[];
  assets: AssetIn[];
  goals: GoalFormRow[];
}

let counter = 0;
function uid(prefix: string): string {
  counter += 1;
  return `${prefix}-${counter}-${Math.abs(hashNow())}`;
}
function hashNow(): number {
  // deterministic-enough unique suffix without Date.now in tests:
  // use a monotonically increasing counter combined with a fixed salt
  return counter * 2654435761;
}

export function emptyForm(): ProfileFormState {
  return {
    id: uid("p"),
    income: { salary: 0, secondary: 0, avg_bonus_monthly: 0, passive: 0 },
    risk: "MEDIUM",
    emergency_fund: 0,
    expenses: [],
    debts: [],
    assets: [],
    goals: [],
  };
}

export function seedToForm(seed: CifSeed): ProfileFormState {
  const f = emptyForm();
  f.income.salary = seed.income;
  const semiFixed: Classification = "SEMI_FIXED";
  f.expenses = [
    { category: "Tổng chi tiêu (từ CIF)", amount: seed.expense, classification: semiFixed },
  ];
  f.debts = [
    {
      name: "Tổng nợ (từ CIF)", monthly_payment: seed.debt_payment, balance: null,
      apr: 0, months_remaining: null, debt_type: "INSTALLMENT",
    },
  ];
  return f;
}

export function toProfileIn(form: ProfileFormState): ProfileIn {
  return {
    id: form.id,
    income: { ...form.income },
    risk: form.risk,
    emergency_fund: form.emergency_fund,
    expenses: form.expenses.map((e) => ({ ...e })),
    debts: form.debts.map((d) => ({ ...d })),
    assets: form.assets.map((a) => ({ ...a })),
    goals: form.goals.map((g) => ({ id: uid("g"), ...g })),
  };
}
```

- [ ] **Step 4: Run — expect PASS**

Run (in `frontend/`): `pnpm test -- profileForm`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/profile/profileForm.ts frontend/src/features/profile/profileForm.test.ts
git commit -m "feat(frontend): add pure profile form model and mappers"
```

---

## Task 13: ProfileBuilder screen

**Files:**
- Create: `frontend/src/features/profile/ProfileBuilder.tsx`
- Test: `frontend/src/features/profile/ProfileBuilder.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/src/features/profile/ProfileBuilder.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ActiveProfileProvider } from "../../state/activeProfile";
import { ProfileBuilder } from "./ProfileBuilder";

afterEach(() => vi.restoreAllMocks());

describe("ProfileBuilder", () => {
  it("submits a profile and reports success", async () => {
    const spy = vi.fn(async () => new Response(JSON.stringify({ id: "p-1-x" }), { status: 201 }));
    vi.stubGlobal("fetch", spy);
    const onCreated = vi.fn();

    render(
      <ActiveProfileProvider>
        <ProfileBuilder initialSeed={null} onCreated={onCreated} />
      </ActiveProfileProvider>,
    );

    await userEvent.click(screen.getByRole("button", { name: /tạo hồ sơ/i }));

    await waitFor(() => expect(spy).toHaveBeenCalled());
    const [url, init] = spy.mock.calls[0];
    expect(url).toBe("/api/profiles");
    expect((init as RequestInit).method).toBe("POST");
    await waitFor(() => expect(onCreated).toHaveBeenCalled());
  });
});
```

- [ ] **Step 2: Run — expect FAIL**

Run (in `frontend/`): `pnpm test -- ProfileBuilder`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement**

```tsx
// frontend/src/features/profile/ProfileBuilder.tsx
import { useState } from "react";
import { createProfile } from "../../api/endpoints";
import type { CifSeed } from "../../api/types";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Field } from "../../components/ui/Field";
import { NumberInput } from "../../components/ui/NumberInput";
import { Select } from "../../components/ui/Select";
import { TextInput } from "../../components/ui/TextInput";
import { useAsync } from "../../hooks/useAsync";
import { useActiveProfile } from "../../state/activeProfile";
import {
  emptyForm, seedToForm, toProfileIn, type GoalFormRow, type ProfileFormState,
} from "./profileForm";

const CLASSES = [
  { value: "FIXED", label: "Cứng" },
  { value: "SEMI_FIXED", label: "Biến đổi" },
  { value: "DISCRETIONARY", label: "Tùy chọn" },
];
const PRIORITIES = [
  { value: "LOW", label: "Thấp" },
  { value: "MEDIUM", label: "Trung bình" },
  { value: "HIGH", label: "Cao" },
  { value: "VERY_HIGH", label: "Rất cao" },
];
const RISKS = [
  { value: "LOW", label: "Thấp" },
  { value: "MEDIUM", label: "Trung bình" },
  { value: "HIGH", label: "Cao" },
];

export function ProfileBuilder({
  initialSeed,
  onCreated,
}: {
  initialSeed: CifSeed | null;
  onCreated: () => void;
}) {
  const [form, setForm] = useState<ProfileFormState>(() =>
    initialSeed ? seedToForm(initialSeed) : emptyForm(),
  );
  const { setActiveProfileId } = useActiveProfile();
  const { run, loading, error } = useAsync(createProfile);

  const update = (patch: Partial<ProfileFormState>) => setForm((f) => ({ ...f, ...patch }));

  async function submit() {
    try {
      const { id } = await run(toProfileIn(form));
      setActiveProfileId(id);
      onCreated();
    } catch {
      /* error surfaced via `error` */
    }
  }

  return (
    <div className="space-y-4">
      {error && <ErrorBanner message={error} />}

      <Card title="Thu nhập (₫/tháng)">
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <Field label="Lương chính">
            <NumberInput ariaLabel="Lương chính" value={form.income.salary}
              onValueChange={(v) => update({ income: { ...form.income, salary: v } })} />
          </Field>
          <Field label="Thu nhập phụ">
            <NumberInput value={form.income.secondary}
              onValueChange={(v) => update({ income: { ...form.income, secondary: v } })} />
          </Field>
          <Field label="Thưởng/tháng">
            <NumberInput value={form.income.avg_bonus_monthly}
              onValueChange={(v) => update({ income: { ...form.income, avg_bonus_monthly: v } })} />
          </Field>
          <Field label="Thu nhập thụ động">
            <NumberInput value={form.income.passive}
              onValueChange={(v) => update({ income: { ...form.income, passive: v } })} />
          </Field>
        </div>
      </Card>

      <Card title="Quỹ khẩn cấp & Khẩu vị rủi ro">
        <div className="grid grid-cols-2 gap-3">
          <Field label="Quỹ khẩn cấp">
            <NumberInput value={form.emergency_fund}
              onValueChange={(v) => update({ emergency_fund: v })} />
          </Field>
          <Field label="Khẩu vị rủi ro">
            <Select value={form.risk} options={RISKS}
              onChange={(e) => update({ risk: e.target.value as ProfileFormState["risk"] })} />
          </Field>
        </div>
      </Card>

      <Card title="Chi tiêu định kỳ">
        <ListEditor
          rows={form.expenses}
          onChange={(expenses) => update({ expenses })}
          empty={{ category: "", amount: 0, classification: "FIXED" }}
          addLabel="Thêm khoản chi"
          render={(row, set) => (
            <>
              <TextInput placeholder="Danh mục" value={row.category}
                onChange={(e) => set({ ...row, category: e.target.value })} />
              <NumberInput value={row.amount} onValueChange={(v) => set({ ...row, amount: v })} />
              <Select value={row.classification} options={CLASSES}
                onChange={(e) => set({ ...row, classification: e.target.value as typeof row.classification })} />
            </>
          )}
        />
      </Card>

      <Card title="Khoản nợ (trả/tháng)">
        <ListEditor
          rows={form.debts}
          onChange={(debts) => update({ debts })}
          empty={{ name: "", monthly_payment: 0, balance: null, apr: 0, months_remaining: null, debt_type: "INSTALLMENT" }}
          addLabel="Thêm khoản nợ"
          render={(row, set) => (
            <>
              <TextInput placeholder="Tên khoản nợ" value={row.name}
                onChange={(e) => set({ ...row, name: e.target.value })} />
              <NumberInput value={row.monthly_payment}
                onValueChange={(v) => set({ ...row, monthly_payment: v })} />
              <Select value={row.debt_type}
                options={[
                  { value: "REVOLVING", label: "Tín dụng xoay vòng" },
                  { value: "INSTALLMENT", label: "Trả góp" },
                  { value: "SECURED", label: "Có tài sản đảm bảo" },
                ]}
                onChange={(e) => set({ ...row, debt_type: e.target.value as typeof row.debt_type })} />
            </>
          )}
        />
      </Card>

      <Card title="Tài sản thanh khoản">
        <ListEditor
          rows={form.assets}
          onChange={(assets) => update({ assets })}
          empty={{ type: "CASH", value: 0, liquidity: "HIGH" }}
          addLabel="Thêm tài sản"
          render={(row, set) => (
            <>
              <Select value={row.type}
                options={[
                  { value: "CASH", label: "Tiền mặt" },
                  { value: "SAVINGS", label: "Tiết kiệm" },
                  { value: "OTHER", label: "Khác" },
                ]}
                onChange={(e) => set({ ...row, type: e.target.value as typeof row.type })} />
              <NumberInput value={row.value} onValueChange={(v) => set({ ...row, value: v })} />
              <Select value={row.liquidity}
                options={[
                  { value: "HIGH", label: "Cao" },
                  { value: "MEDIUM", label: "Trung bình" },
                  { value: "LOW", label: "Thấp" },
                ]}
                onChange={(e) => set({ ...row, liquidity: e.target.value as typeof row.liquidity })} />
            </>
          )}
        />
      </Card>

      <Card title="Mục tiêu tài chính">
        <ListEditor<GoalFormRow>
          rows={form.goals}
          onChange={(goals) => update({ goals })}
          empty={{ name: "", target_amount: 0, deadline: "2030-01-01", priority: "MEDIUM", savings_allocated: 0 }}
          addLabel="Thêm mục tiêu"
          render={(row, set) => (
            <>
              <TextInput placeholder="Tên mục tiêu" value={row.name}
                onChange={(e) => set({ ...row, name: e.target.value })} />
              <NumberInput value={row.target_amount}
                onValueChange={(v) => set({ ...row, target_amount: v })} />
              <input type="date" value={row.deadline}
                onChange={(e) => set({ ...row, deadline: e.target.value })}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              <Select value={row.priority} options={PRIORITIES}
                onChange={(e) => set({ ...row, priority: e.target.value as typeof row.priority })} />
            </>
          )}
        />
      </Card>

      <Button onClick={submit} disabled={loading}>
        {loading ? "Đang tạo…" : "Tạo hồ sơ"}
      </Button>
    </div>
  );
}

function ListEditor<T>({
  rows, onChange, empty, addLabel, render,
}: {
  rows: T[];
  onChange: (rows: T[]) => void;
  empty: T;
  addLabel: string;
  render: (row: T, set: (next: T) => void) => React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      {rows.map((row, i) => (
        <div key={i} className="flex flex-wrap items-center gap-2">
          {render(row, (next) => onChange(rows.map((r, j) => (j === i ? next : r))))}
          <Button variant="ghost" onClick={() => onChange(rows.filter((_, j) => j !== i))}>
            Xóa
          </Button>
        </div>
      ))}
      <Button variant="ghost" onClick={() => onChange([...rows, { ...empty }])}>
        {addLabel}
      </Button>
    </div>
  );
}
```

- [ ] **Step 4: Run — expect PASS**

Run (in `frontend/`): `pnpm test -- ProfileBuilder`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/profile/ProfileBuilder.tsx frontend/src/features/profile/ProfileBuilder.test.tsx
git commit -m "feat(frontend): add ProfileBuilder screen"
```

---

## Task 14: AnalysisDashboard screen

**Files:**
- Create: `frontend/src/features/analysis/AnalysisDashboard.tsx`
- Test: `frontend/src/features/analysis/AnalysisDashboard.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/src/features/analysis/AnalysisDashboard.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { MetricsOut } from "../../api/types";
import { AnalysisDashboard } from "./AnalysisDashboard";

afterEach(() => vi.restoreAllMocks());

const METRICS: MetricsOut = {
  ncf: 1_200_000, dti: 37.93, dti_band: "WARNING", saving_rate: 8.28,
  efr: 2.94, pgrs: 100,
  goals: [{ goal_id: "g1", name: "Car", gap: 300_000_000, monthly_allocated: 400_000,
            gat: 750, delay: 720, grs: 100, months_remaining: 30 }],
  flags: [],
};

describe("AnalysisDashboard", () => {
  it("renders metrics from the API", async () => {
    vi.stubGlobal("fetch", vi.fn(async () =>
      new Response(JSON.stringify(METRICS), { status: 200 })));
    render(<AnalysisDashboard profileId="p1" />);
    await waitFor(() => expect(screen.getByText(/1\.200\.000 ₫/)).toBeInTheDocument());
    expect(screen.getByText("WARNING")).toBeInTheDocument();
    expect(screen.getByText("Car")).toBeInTheDocument();
  });

  it("shows an error banner on failure", async () => {
    vi.stubGlobal("fetch", vi.fn(async () =>
      new Response(JSON.stringify({ detail: "Profile not found: p1" }), { status: 404 })));
    render(<AnalysisDashboard profileId="p1" />);
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent(/not found/i));
  });
});
```

- [ ] **Step 2: Run — expect FAIL**

Run (in `frontend/`): `pnpm test -- AnalysisDashboard`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement**

```tsx
// frontend/src/features/analysis/AnalysisDashboard.tsx
import { useEffect } from "react";
import { getAnalysis } from "../../api/endpoints";
import { Badge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Metric } from "../../components/ui/Metric";
import { Spinner } from "../../components/ui/Spinner";
import { useAsync } from "../../hooks/useAsync";
import { dtiBandClass, riskClass } from "../../lib/bands";
import { formatVnd } from "../../lib/money";

export function AnalysisDashboard({ profileId }: { profileId: string }) {
  const { run, data, loading, error } = useAsync(getAnalysis);

  useEffect(() => {
    run(profileId).catch(() => undefined);
  }, [run, profileId]);

  if (loading) return <Spinner />;
  if (error) return <ErrorBanner message={error} />;
  if (!data) return null;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
        <Metric label="Dòng tiền ròng (NCF)" value={formatVnd(data.ncf)} />
        <Metric
          label="DTI"
          value={`${data.dti.toFixed(1)}%`}
          hint={<Badge className={dtiBandClass(data.dti_band)}>{data.dti_band}</Badge>}
        />
        <Metric label="Tỷ lệ tiết kiệm" value={`${data.saving_rate.toFixed(1)}%`}
          hint="Khuyến nghị ≥ 20%" />
        <Metric label="Quỹ khẩn cấp (EFR)" value={`${data.efr.toFixed(2)} tháng`}
          hint="An toàn ≥ 3 tháng" />
        <Metric label="Rủi ro danh mục (PGRS)" value={data.pgrs.toFixed(0)}
          hint={<Badge className={riskClass(data.pgrs)}>{data.pgrs.toFixed(0)}/100</Badge>} />
      </div>

      {data.flags.length > 0 && (
        <ErrorBanner message={`Cảnh báo: ${data.flags.join(", ")}`} />
      )}

      <Card title="Mục tiêu">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-500">
              <th className="py-1">Mục tiêu</th>
              <th>Còn thiếu</th>
              <th>Phân bổ/tháng</th>
              <th>Còn lại (tháng)</th>
              <th>Rủi ro</th>
            </tr>
          </thead>
          <tbody>
            {data.goals.map((g) => (
              <tr key={g.goal_id} className="border-t border-slate-100">
                <td className="py-2">{g.name}</td>
                <td>{formatVnd(g.gap)}</td>
                <td>{formatVnd(g.monthly_allocated)}</td>
                <td>{g.months_remaining}</td>
                <td><Badge className={riskClass(g.grs)}>{g.grs.toFixed(0)}</Badge></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
```

- [ ] **Step 4: Run — expect PASS**

Run (in `frontend/`): `pnpm test -- AnalysisDashboard`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/analysis
git commit -m "feat(frontend): add AnalysisDashboard screen"
```

---

## Task 15: PurchaseEvaluator screen

**Files:**
- Create: `frontend/src/features/advisory/PurchaseEvaluator.tsx`
- Test: `frontend/src/features/advisory/PurchaseEvaluator.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/src/features/advisory/PurchaseEvaluator.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { EvaluateOut } from "../../api/types";
import { PurchaseEvaluator } from "./PurchaseEvaluator";

afterEach(() => vi.restoreAllMocks());

const RESULT: EvaluateOut = {
  best_option_id: "installment_12", summary: "Nên trả góp 12 tháng",
  scorer_used: "deterministic",
  options: [
    { option_id: "installment_12", risk_score: 45, recommended: true,
      explanation: "Bảo toàn dòng tiền", key_factors: ["dòng tiền"], monthly_payment: 1_250_000,
      ncf_new: -50_000, dti_new: 46.5, efr_after: 2.94, delta_pgrs: 8, flags: [] },
    { option_id: "full", risk_score: 80, recommended: false,
      explanation: "Âm dòng tiền", key_factors: [], monthly_payment: 0,
      ncf_new: -13_800_000, dti_new: 37.9, efr_after: 0.64, delta_pgrs: 0,
      flags: ["NEGATIVE_CASHFLOW"] },
  ],
};

describe("PurchaseEvaluator", () => {
  it("evaluates and renders ranked options", async () => {
    vi.stubGlobal("fetch", vi.fn(async () =>
      new Response(JSON.stringify(RESULT), { status: 200 })));
    render(<PurchaseEvaluator profileId="p1" />);

    await userEvent.type(screen.getByLabelText(/tên món/i), "Điện thoại");
    await userEvent.type(screen.getByLabelText(/giá/i), "15.000.000");
    await userEvent.click(screen.getByRole("button", { name: /đánh giá/i }));

    await waitFor(() => expect(screen.getByText(/Nên trả góp 12 tháng/)).toBeInTheDocument());
    expect(screen.getByText("installment_12")).toBeInTheDocument();
    expect(screen.getByText(/NEGATIVE_CASHFLOW/)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run — expect FAIL**

Run (in `frontend/`): `pnpm test -- PurchaseEvaluator`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement**

```tsx
// frontend/src/features/advisory/PurchaseEvaluator.tsx
import { useState } from "react";
import { evaluatePurchase } from "../../api/endpoints";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Field } from "../../components/ui/Field";
import { NumberInput } from "../../components/ui/NumberInput";
import { TextInput } from "../../components/ui/TextInput";
import { useAsync } from "../../hooks/useAsync";
import { riskClass } from "../../lib/bands";
import { formatVnd } from "../../lib/money";

export function PurchaseEvaluator({ profileId }: { profileId: string }) {
  const [item, setItem] = useState("");
  const [amount, setAmount] = useState(0);
  const { run, data, loading, error } = useAsync(evaluatePurchase);

  async function submit() {
    await run({
      profile_id: profileId, item_name: item || "Món hàng",
      purchase_amount: amount, candidate_plans: null,
    }).catch(() => undefined);
  }

  const ranked = data
    ? [...data.options].sort((a, b) => Number(b.recommended) - Number(a.recommended) || a.risk_score - b.risk_score)
    : [];

  return (
    <div className="space-y-4">
      {error && <ErrorBanner message={error} />}
      <Card title="Khoản mua mới">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <Field label="Tên món hàng">
            <TextInput aria-label="Tên món hàng" value={item}
              onChange={(e) => setItem(e.target.value)} />
          </Field>
          <Field label="Giá (₫)">
            <NumberInput ariaLabel="Giá" value={amount} onValueChange={setAmount} />
          </Field>
          <div className="flex items-end">
            <Button onClick={submit} disabled={loading || amount <= 0}>
              {loading ? "Đang đánh giá…" : "Đánh giá"}
            </Button>
          </div>
        </div>
      </Card>

      {data && (
        <Card title="Kết quả">
          <p className="text-sm text-slate-700">
            <strong>Đề xuất:</strong> {data.summary}{" "}
            <span className="ml-2 rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
              nguồn điểm: {data.scorer_used}
            </span>
          </p>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {ranked.map((o) => (
          <div key={o.option_id}
            className={`rounded-xl border bg-white p-4 ${o.option_id === data?.best_option_id ? "border-indigo-400 ring-1 ring-indigo-200" : "border-slate-200"}`}>
            <div className="flex items-center justify-between">
              <span className="font-semibold">{o.option_id}</span>
              <Badge className={riskClass(o.risk_score)}>Rủi ro {o.risk_score.toFixed(0)}</Badge>
            </div>
            <p className="mt-2 text-sm text-slate-600">{o.explanation}</p>
            <dl className="mt-3 grid grid-cols-2 gap-1 text-xs text-slate-500">
              <dt>Trả/tháng</dt><dd className="text-right text-slate-700">{formatVnd(o.monthly_payment)}</dd>
              <dt>NCF mới</dt><dd className="text-right text-slate-700">{formatVnd(o.ncf_new)}</dd>
              <dt>DTI mới</dt><dd className="text-right text-slate-700">{o.dti_new.toFixed(1)}%</dd>
              <dt>EFR sau</dt><dd className="text-right text-slate-700">{o.efr_after.toFixed(2)}</dd>
              <dt>ΔPGRS</dt><dd className="text-right text-slate-700">{o.delta_pgrs.toFixed(1)}</dd>
            </dl>
            {o.flags.length > 0 && (
              <div className="mt-2 text-xs font-medium text-red-600">{o.flags.join(", ")}</div>
            )}
            {!o.recommended && (
              <div className="mt-1 text-xs text-slate-400">Không khuyến nghị</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run — expect PASS**

Run (in `frontend/`): `pnpm test -- PurchaseEvaluator`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/advisory
git commit -m "feat(frontend): add PurchaseEvaluator screen"
```

---

## Task 16: CifImport screen

**Files:**
- Create: `frontend/src/features/ingestion/CifImport.tsx`
- Test: `frontend/src/features/ingestion/CifImport.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/src/features/ingestion/CifImport.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { CifSeed } from "../../api/types";
import { CifImport } from "./CifImport";

afterEach(() => vi.restoreAllMocks());

describe("CifImport", () => {
  it("lists CIFs and emits a seed on selection", async () => {
    const seed: CifSeed = { cif: "100", income: 12_000_000, expense: 5_000_000, debt_payment: 2_000_000 };
    vi.stubGlobal("fetch", vi.fn(async (url: string) => {
      if (url.includes("/ingestion/cifs")) {
        return new Response(JSON.stringify({ cifs: ["100", "200"] }), { status: 200 });
      }
      return new Response(JSON.stringify(seed), { status: 200 });
    }));
    const onSeed = vi.fn();

    render(<CifImport onSeed={onSeed} />);
    await waitFor(() => expect(screen.getByRole("option", { name: "100" })).toBeInTheDocument());

    await userEvent.click(screen.getByRole("button", { name: /dùng dữ liệu/i }));
    await waitFor(() => expect(onSeed).toHaveBeenCalledWith(seed));
  });
});
```

- [ ] **Step 2: Run — expect FAIL**

Run (in `frontend/`): `pnpm test -- CifImport`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement**

```tsx
// frontend/src/features/ingestion/CifImport.tsx
import { useEffect, useState } from "react";
import { getCifSeed, listCifs } from "../../api/endpoints";
import type { CifSeed } from "../../api/types";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Field } from "../../components/ui/Field";
import { Select } from "../../components/ui/Select";
import { Spinner } from "../../components/ui/Spinner";
import { useAsync } from "../../hooks/useAsync";
import { formatVnd } from "../../lib/money";

export function CifImport({ onSeed }: { onSeed: (seed: CifSeed) => void }) {
  const list = useAsync(listCifs);
  const seedCall = useAsync(getCifSeed);
  const [cif, setCif] = useState("");
  const [strategy, setStrategy] = useState<"latest" | "average">("latest");

  useEffect(() => {
    list.run().then((cifs) => setCif(cifs[0] ?? "")).catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function use() {
    if (!cif) return;
    const seed = await seedCall.run(cif, strategy).catch(() => null);
    if (seed) onSeed(seed);
  }

  if (list.loading) return <Spinner />;

  return (
    <div className="space-y-4">
      {(list.error || seedCall.error) && (
        <ErrorBanner message={list.error ?? seedCall.error ?? ""} />
      )}
      <Card title="Nhập dữ liệu từ CIF ngân hàng">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <Field label="Chọn CIF">
            <Select value={cif} onChange={(e) => setCif(e.target.value)}
              options={(list.data ?? []).map((c) => ({ value: c, label: c }))} />
          </Field>
          <Field label="Cách tính">
            <Select value={strategy}
              onChange={(e) => setStrategy(e.target.value as "latest" | "average")}
              options={[
                { value: "latest", label: "Tháng gần nhất" },
                { value: "average", label: "Trung bình" },
              ]} />
          </Field>
          <div className="flex items-end">
            <Button onClick={use} disabled={!cif || seedCall.loading}>
              {seedCall.loading ? "Đang lấy…" : "Dùng dữ liệu này"}
            </Button>
          </div>
        </div>
        {seedCall.data && (
          <p className="mt-3 text-sm text-slate-600">
            Thu nhập {formatVnd(seedCall.data.income)} · Chi tiêu{" "}
            {formatVnd(seedCall.data.expense)} · Nợ {formatVnd(seedCall.data.debt_payment)}
          </p>
        )}
      </Card>
    </div>
  );
}
```

- [ ] **Step 4: Run — expect PASS**

Run (in `frontend/`): `pnpm test -- CifImport`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/ingestion
git commit -m "feat(frontend): add CifImport screen"
```

---

## Task 17: App shell + main entry

**Files:**
- Create: `frontend/src/App.tsx`, `frontend/src/main.tsx`
- Test: `frontend/src/App.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/src/App.test.tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { App } from "./App";

describe("App", () => {
  it("renders the nav with four sections", () => {
    render(<App />);
    expect(screen.getByRole("button", { name: /nhập CIF/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /hồ sơ/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /phân tích/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /đánh giá/i })).toBeInTheDocument();
  });

  it("shows a hint when no active profile for analysis", async () => {
    localStorage.clear();
    render(<App />);
    // default section is Import; switching to Analysis without a profile shows hint
    screen.getByRole("button", { name: /phân tích/i }).click();
    expect(await screen.findByText(/chưa có hồ sơ/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run — expect FAIL**

Run (in `frontend/`): `pnpm test -- App`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement**

```tsx
// frontend/src/App.tsx
import { useState } from "react";
import type { CifSeed } from "./api/types";
import { Button } from "./components/ui/Button";
import { AnalysisDashboard } from "./features/analysis/AnalysisDashboard";
import { PurchaseEvaluator } from "./features/advisory/PurchaseEvaluator";
import { CifImport } from "./features/ingestion/CifImport";
import { ProfileBuilder } from "./features/profile/ProfileBuilder";
import { ActiveProfileProvider, useActiveProfile } from "./state/activeProfile";

type Section = "import" | "profile" | "analysis" | "evaluate";

const TABS: { key: Section; label: string }[] = [
  { key: "import", label: "1. Nhập CIF" },
  { key: "profile", label: "2. Hồ sơ" },
  { key: "analysis", label: "3. Phân tích" },
  { key: "evaluate", label: "4. Đánh giá" },
];

function Shell() {
  const [section, setSection] = useState<Section>("import");
  const [seed, setSeed] = useState<CifSeed | null>(null);
  const { activeProfileId } = useActiveProfile();

  return (
    <div className="mx-auto max-w-4xl p-6">
      <h1 className="mb-1 text-2xl font-bold text-slate-800">BNPL Assistant</h1>
      <p className="mb-5 text-sm text-slate-500">Tư vấn tài chính cá nhân</p>

      <nav className="mb-6 flex flex-wrap gap-2">
        {TABS.map((t) => (
          <Button key={t.key}
            variant={section === t.key ? "primary" : "ghost"}
            onClick={() => setSection(t.key)}>
            {t.label}
          </Button>
        ))}
      </nav>

      {section === "import" && (
        <CifImport onSeed={(s) => { setSeed(s); setSection("profile"); }} />
      )}
      {section === "profile" && (
        <ProfileBuilder initialSeed={seed} onCreated={() => setSection("analysis")} />
      )}
      {section === "analysis" && (
        activeProfileId
          ? <AnalysisDashboard profileId={activeProfileId} />
          : <NoProfile />
      )}
      {section === "evaluate" && (
        activeProfileId
          ? <PurchaseEvaluator profileId={activeProfileId} />
          : <NoProfile />
      )}
    </div>
  );
}

function NoProfile() {
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
      Chưa có hồ sơ. Hãy tạo hồ sơ ở bước 2 trước.
    </div>
  );
}

export function App() {
  return (
    <ActiveProfileProvider>
      <Shell />
    </ActiveProfileProvider>
  );
}
```

```tsx
// frontend/src/main.tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
```

- [ ] **Step 4: Run — expect PASS, then full gate**

Run (in `frontend/`): `pnpm test -- App`
Expected: PASS.
Run: `pnpm test && pnpm exec tsc --noEmit`
Expected: all tests pass; tsc clean.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.tsx frontend/src/main.tsx frontend/src/App.test.tsx
git commit -m "feat(frontend): add app shell, navigation, and entry point"
```

---

## Task 18: README + final verification

**Files:**
- Modify: `README.md` (add a Frontend section)

- [ ] **Step 1: Append a Frontend section to `README.md`**

````markdown
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
````

- [ ] **Step 2: Run the full gate (backend + frontend)**

Run (repo root): `ruff check app && mypy app && python -m pytest -q`
Expected: clean; all pass (Postgres test skips).
Run (in `frontend/`): `pnpm test && pnpm exec tsc --noEmit`
Expected: all tests pass; tsc clean.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add frontend setup and run instructions"
```

---

## Self-review checklist (completed during planning)

- **Spec coverage:** CORS + ingestion API + config (Tasks 1–3); Vite/TS/Tailwind scaffold (Task 4); types mirroring backend (Task 5); typed client + ApiError (Task 6); endpoints (Task 7); money/bands (Task 8); useAsync (Task 9); UI kit (Task 10); activeProfile context (Task 11); pure form mapper incl. seedToForm (Task 12); ProfileBuilder (Task 13); AnalysisDashboard (Task 14); PurchaseEvaluator (Task 15); CifImport (Task 16); App shell + nav + no-profile hint (Task 17); README + gate (Task 18).
- **Type consistency:** `apiFetch<T>`, `ApiError{status,detail}`, endpoint signatures (`createProfile`/`getAnalysis`/`evaluatePurchase`/`listCifs`/`getCifSeed`), `ProfileFormState`/`toProfileIn`/`seedToForm`, `useActiveProfile().{activeProfileId,setActiveProfileId}`, `useAsync().{run,data,loading,error}` referenced identically across tasks. Backend: `IngestionService.{list_cifs,get_seed}`, `deps.get_ingestion_service`, `CifNotFound`, `cors_origin_list` consistent.
- **Backend test isolation:** ingestion API test monkeypatches `deps.get_ingestion_service`; router calls it via the `deps` module attribute so the patch takes effect (Task 3 note).
- **Determinism:** `profileForm.ts` avoids `Date.now()` for ids (counter-based) so tests are stable; the `uid` suffix is derived from the counter.

---

## Execution handoff

Plan complete. Two execution options:

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between batches.
2. **Inline Execution** — task-by-task with checkpoints.
