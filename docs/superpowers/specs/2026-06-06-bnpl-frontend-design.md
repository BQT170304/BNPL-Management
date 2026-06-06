# BNPL Assistant Frontend — Design Spec

**Version:** 1.0
**Date:** 2026-06-06
**Status:** Approved
**Backend spec:** `docs/superpowers/specs/2026-06-06-bnpl-assistant-design.md`

---

## 1. Purpose

A browser UI for the BNPL Assistant MVP that connects to the FastAPI backend. Four
flows: optionally **seed a profile from CIF banking data**, **build/submit a
financial profile**, **view the analysis dashboard**, and **evaluate a purchase**
across payment options with risk scores and an explanation.

## 2. Stack

React 18 + TypeScript (strict) + Vite + Tailwind CSS. Plain `fetch` via a typed
client and a generic async hook (no TanStack Query). Vitest + React Testing
Library for focused tests. Package manager: pnpm.

## 3. Backend additions (required for the frontend)

These extend the existing modular monolith, following its clean-architecture
patterns. They are additive — no change to domain or existing scoring code.

### 3.1 CORS
`app/main.py` adds `CORSMiddleware` with origins from config
(`CORS_ORIGINS`, default `http://localhost:5173`).

### 3.2 Ingestion HTTP API
New `app/modules/ingestion/api/{router,schemas}.py` plus an application service
`IngestionService` that wraps the existing `CsvSummarySource` + `derive_seed`:

- `GET /ingestion/cifs` → `{ "cifs": string[] }` — distinct CIF ids from the
  server-side summary CSV.
- `GET /ingestion/cif/{cif}/seed?strategy=latest|average` →
  `{ "cif": string, "income": int, "expense": int, "debt_payment": int }`.
  Unknown cif → 404 (`CifNotFound` domain error).

The CSV is loaded once and cached in the service (path from
`INGESTION_CSV_PATH`, default `summary_by_cif_month.csv`). No new
profile-construction endpoint: the frontend maps a seed into the profile form and
the user submits the normal `POST /profiles`.

### 3.3 Config additions (`app/core/config.py`)
- `cors_origins: str = "http://localhost:5173"` (comma-separated → list)
- `ingestion_csv_path: str = "summary_by_cif_month.csv"`

### 3.4 Errors (`app/core/errors.py`)
- `CifNotFound(DomainError)` → mapped to 404 in `main.py`.

### 3.5 DI (`app/dependencies.py`)
- `get_ingestion_service()` builds `IngestionService(CsvSummarySource(), settings)`,
  memoized (module-level singleton) so the CSV is parsed once.

## 4. Frontend architecture

```
frontend/
  index.html
  package.json  tsconfig.json  vite.config.ts  tailwind.config.js  postcss.config.js
  src/
    main.tsx            # mounts <App/>
    App.tsx             # top nav (Import → Profile → Analysis → Evaluate) + active section
    index.css           # tailwind directives
    api/
      types.ts          # TS types mirroring backend schemas (single source of truth)
      client.ts         # apiFetch<T>() typed wrapper + ApiError
      endpoints.ts      # createProfile, getAnalysis, evaluatePurchase, listCifs, getCifSeed
    hooks/
      useAsync.ts       # generic { run, data, loading, error }
    lib/
      money.ts          # formatVnd(int) -> "14.500.000 ₫"; parseVnd(str) -> int
      bands.ts          # dtiBandColor(band); riskColor(score); badge class helpers
    state/
      activeProfile.tsx # context: activeProfileId + setter, persisted to localStorage
    components/ui/
      Card.tsx Badge.tsx Button.tsx TextInput.tsx NumberInput.tsx Select.tsx
      Field.tsx Spinner.tsx ErrorBanner.tsx Metric.tsx
    features/
      ingestion/CifImport.tsx
      profile/ProfileBuilder.tsx
      profile/profileForm.ts        # form state types + toProfileIn() mapper + seed→form
      analysis/AnalysisDashboard.tsx
      advisory/PurchaseEvaluator.tsx
  test setup: vitest.config.ts, src/test/setup.ts
```

### 4.1 Units & responsibilities
- **`api/types.ts`** — exact mirrors of backend Pydantic schemas (ProfileIn,
  MetricsOut, EvaluateIn/Out, CifSeed, enums). One source of truth for shapes.
- **`api/client.ts`** — `apiFetch<T>(path, init?)`: prefixes `/api`, sets JSON
  headers, parses JSON, throws `ApiError{status, detail}` on non-2xx. No UI.
- **`api/endpoints.ts`** — one typed function per backend call. No React.
- **`hooks/useAsync.ts`** — wraps an async fn → `{ run, data, loading, error }`,
  guards against setState after unmount. Used by every screen for loading/error.
- **`lib/money.ts`, `lib/bands.ts`** — pure helpers; unit-tested.
- **`state/activeProfile.tsx`** — React context holding the created profile's id so
  Analysis/Evaluate know which profile to query; persisted to localStorage.
- **`features/profile/profileForm.ts`** — pure: form-state types, `toProfileIn`
  (form → API body, parsing VND strings to ints, deriving goal ids), and
  `seedToForm` (CifSeed → prefilled form with one aggregate expense + one aggregate
  debt the user can edit). Pure → unit-tested.
- **feature components** — compose UI + hooks; each owns one screen.

### 4.2 Navigation & shared state
`App.tsx` renders a top nav with four sections and a local `section` state
(no router dependency — YAGNI for 4 tabs). `ActiveProfileProvider` wraps the app.
Flow: CifImport (optional) writes a seed into a shared "pending seed" passed to
ProfileBuilder; ProfileBuilder on success calls `setActiveProfileId(id)` and
switches to Analysis. Analysis and Evaluate are disabled until an active profile
exists (nav shows a hint).

### 4.3 Data flow per screen
- **CifImport:** `listCifs()` on mount → select a CIF + strategy → `getCifSeed()`
  → "Dùng dữ liệu này" stores the seed and navigates to Profile (prefilled).
- **ProfileBuilder:** controlled form (income, dynamic lists for expenses/debts/
  assets/goals, EF, risk). Submit → `toProfileIn` → `createProfile` → on success
  set active id, go to Analysis. Validation: salary ≥ 0 required, target ≥ 0, etc.
- **AnalysisDashboard:** on active id → `getAnalysis(id)` → metric cards (NCF, DTI
  + band badge, saving rate vs 20% target, EFR vs 3-month line, PGRS) + per-goal
  table (gap, monthly allocated, GAT, delay, GRS badge) + flags banner.
- **PurchaseEvaluator:** item + price (+ optional plans) → `evaluatePurchase` →
  ranked option cards (sorted by risk asc, blocked last), each showing risk badge,
  monthly payment, ncf_new, dti_new, efr_after, ΔPGRS, flags, explanation; header
  shows best option + summary + `scorer_used` chip.

### 4.4 Styling
Tailwind, light theme, card-based. Color tokens by band/score:
`SAFE`/low-risk → green, `ACCEPTABLE` → blue, `WARNING` → amber, `DANGER`/high →
red. Risk score → green ≤25, blue ≤50, amber ≤75, red >75. Vietnamese labels;
all money via `formatVnd`.

## 5. Error handling
- `ApiError` carries `status` + `detail`. `useAsync` exposes `error`.
- Screens render `<ErrorBanner>` with a friendly message; 404 → "Không tìm thấy…",
  400 → show backend `detail`, network → "Không kết nối được máy chủ".
- Forms block submit while loading; disable nav actions that need a profile when
  none is active.

## 6. Dev / build
- `vite.config.ts` proxies `/api` → `http://localhost:8000` (so `client.ts` uses
  relative `/api`, no CORS issue in dev; CORS still added backend-side for non-proxy
  deployments).
- Scripts: `pnpm dev`, `pnpm build`, `pnpm test`, `pnpm lint` (eslint + tsc).
- README: how to run backend (`uvicorn app.main:app`) + frontend (`pnpm dev`).

## 7. Testing
- **Unit (Vitest):** `money.ts` (format/parse round-trip), `bands.ts` (boundary
  colors), `client.ts` (2xx parse; non-2xx → ApiError via mocked fetch),
  `profileForm.ts` (`toProfileIn` parses VND + builds correct body; `seedToForm`).
- **Component (RTL):** ProfileBuilder submit happy path (mock fetch → asserts
  createProfile called with mapped body, active id set); AnalysisDashboard renders
  metrics from a mocked response; PurchaseEvaluator renders ranked options.
- **Backend:** unit-test `IngestionService` (list cifs, seed latest/average,
  unknown cif → CifNotFound) and an integration test for the two ingestion routes
  using a tiny temp CSV.

## 8. Out of scope (MVP)
Auth, multi-profile management UI, editing an existing profile via API (no backend
PUT yet), routing library, charts/graphs (numbers + badges only), i18n toggle
(Vietnamese only), deployment config.

## 9. Open assumptions
1. CIF seed maps to **one aggregate SEMI_FIXED expense + one aggregate debt** in the
   prefilled form; the user edits before submitting. §4.1.
2. `GET /ingestion/cifs` returns all distinct CIFs (dataset is small); no
   pagination. §3.2.
3. Dev uses the Vite proxy; production would set `CORS_ORIGINS`. §6.
