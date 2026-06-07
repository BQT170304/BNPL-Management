# BNPL Assistant Frontend — Design Spec (As-Built)

**Version:** 2.0
**Date cập nhật:** 2026-06-06
**Trạng thái:** Đã triển khai — tài liệu phản ánh code hiện tại
**Backend spec:** `docs/superpowers/specs/2026-06-06-bnpl-assistant-design.md`

---

## 1. Mục đích

SPA tư vấn tài chính cá nhân kết nối với FastAPI backend. Các luồng chính:
1. **Đăng nhập** — màn hình login, lưu Bearer token.
2. **Onboard hồ sơ** — wizard 2 bước: upload file giao dịch → xem lại & lưu hồ sơ.
3. **Dashboard** — sức khoẻ tài chính, cảnh báo, mục tiêu (sidebar) + đánh giá mua sắm (main).
4. **Dự báo** — biểu đồ Prophet theo tuần (khi có dữ liệu giao dịch).
5. **Cập nhật hồ sơ** — wizard tương tự onboard, lưu vào hồ sơ hiện tại.

---

## 2. Tech Stack

React 18 + TypeScript (strict) + Vite + Tailwind CSS. Plain `fetch` qua typed client + generic async hook. Vitest + React Testing Library. npm.

Vite proxy: `/api` → `http://localhost:8000`.

---

## 3. Cấu trúc thư mục

```
frontend/src/
  main.tsx
  App.tsx                        # routing state + wizard orchestration
  api/
    types.ts                     # mirrors backend Pydantic schemas
    client.ts                    # apiFetch<T>, ApiError, getToken
    endpoints.ts                 # typed functions per API call
  hooks/
    useAsync.ts                  # { run, data, loading, error }
  lib/
    money.ts                     # formatVnd, parseVnd
    bands.ts                     # dtiBandColor, riskColor
  state/
    auth.tsx                     # AuthContext: token, login, logout (localStorage)
    activeProfile.tsx            # activeProfileId, setActiveProfileId, resetProfile
  components/ui/
    Button, Card, Badge, TextInput, NumberInput, Select,
    Field, Spinner, ErrorBanner, Metric
  features/
    auth/
      LoginScreen.tsx
    ingestion/
      TransactionImport.tsx      # drag-drop file upload, gọi /profiles/extract
    profile/
      ProfileBuilder.tsx         # form đầy đủ (income, expenses, debts, assets, goals)
      profileForm.ts             # pure: form state types, toProfileIn, seedToForm
    analysis/
      HealthSidebar.tsx          # NCF, DTI, EFR, PGRS + Alerts + Goals
    advisory/
      PurchaseEvaluator.tsx      # nhập mua sắm, xem phương án + risk scores
    forecasting/
      ForecastSection.tsx        # biểu đồ Prophet theo tuần + target line
```

---

## 4. Luồng ứng dụng

### 4.1 Authentication

- **LoginScreen**: `POST /auth/login` → lưu token vào `localStorage["bnpl.token"]`.
- **AuthProvider**: cung cấp `{ token, login, logout }` toàn app.
- `apiFetch` tự động đính kèm `Authorization: Bearer <token>`.
- Logout: xoá token, quay về LoginScreen.

### 4.2 Onboarding (lần đầu, chưa có hồ sơ)

Wizard 2 bước, quản lý bởi `Shell` trong `App.tsx`:

```
Bước 1: Nhập file giao dịch
  └─ [TransactionImport]
      ├─ Drag & drop hoặc click upload CSV/XLSX
      ├─ Gọi POST /profiles/extract (multipart/form-data)
      ├─ Hiện tóm tắt: thu nhập trung bình, chi tiêu, tiền còn lại
      ├─ "Xem lại & Lưu hồ sơ →" → Bước 2
      └─ "Bỏ qua — nhập thông tin thủ công" → Bước 2 (form trống)

Bước 2: Xem lại hồ sơ
  └─ [ProfileBuilder] mode="create"
      ├─ Pre-fill từ extracted profile (income, expenses, debts)
      ├─ emergency_fund = 0, goals = [] → user tự nhập
      ├─ "← Quay lại nhập file" → Bước 1
      └─ Lưu → POST /profiles → setActiveProfileId → Dashboard
```

### 4.3 Dashboard (đã có hồ sơ)

```
Header: "BNPL Assistant" | "Đăng xuất"

Layout (max-w-6xl):
  ┌─────────────────────┬──────────────────────────────┐
  │  HealthSidebar      │  PurchaseEvaluator           │
  │  (w-72, sticky)     │  (flex-1)                    │
  │                     │                              │
  │  • NCF / tháng      │  Nhập mua sắm                │
  │  • Tỷ lệ tiết kiệm  │  → Phương án trả góp         │
  │  • Tỷ lệ nợ (DTI)  │  → Risk scores               │
  │  • Dự phòng (EFR)   │  → Giải thích                │
  │  • Rủi ro (PGRS)    │                              │
  │  ────────────────── │                              │
  │  Cảnh báo           │                              │
  │  ────────────────── │                              │
  │  Mục tiêu           │                              │
  │  [Cập nhật hồ sơ]   │                              │
  └─────────────────────┴──────────────────────────────┘

  ForecastSection (full width, chỉ hiện khi có importedCif)
```

### 4.4 Cập nhật hồ sơ

Nút "Sửa hồ sơ" trong HealthSidebar mở **UpdateWizard** (cùng 2 bước như onboard):

```
Bước 1: Nhập file giao dịch mới (hoặc bỏ qua)
Bước 2: Xem lại hồ sơ
  └─ [ProfileBuilder] mode="update"
      ├─ initialProfile = merge(extractedProfile, currentProfile)
      │   (id, goals, debts từ currentProfile; income/expenses từ extracted)
      ├─ PUT /profiles/{id}
      └─ Lưu → quay về Dashboard
```

Nút "Huỷ" ở header wizard → quay về Dashboard không lưu.

**Không có nút "Đổi hồ sơ"** — mỗi account chỉ có một hồ sơ, chỉ cập nhật không thay thế.

---

## 5. Components chi tiết

### 5.1 HealthSidebar

- `GET /profiles/{id}/analysis` → NCF, DTI, DTI_band, saving_rate, EFR, PGRS, goals.
- `GET /profiles/{id}/alerts` → danh sách cảnh báo + `has_critical`.
- Error 404 → gọi `onProfileNotFound()` → reset profile ID → quay Onboarding.
- Màu sắc DTI: SAFE=emerald, ACCEPTABLE=blue, WARNING=amber, DANGER=red.
- EFR màu: ≥3 emerald, ≥1 amber, <1 red.

**Nhãn hiển thị** (không dùng thuật ngữ kỹ thuật):
- NCF → "Tiền còn lại / tháng"
- DTI → "Tỷ lệ nợ"
- EFR → "Dự phòng"
- PGRS → "Rủi ro"

### 5.2 PurchaseEvaluator

- Nhập: tên mặt hàng, giá (VND).
- `POST /advisory/evaluate` → danh sách phương án xếp theo risk_score tăng dần.
- Mỗi phương án hiện: risk badge, "Tiền còn lại / tháng", "Tỷ lệ nợ mới", "Tháng tiền âm", giải thích.
- Phương án vi phạm hard rule (negative NCF) → mark last, không recommend.

### 5.3 ForecastSection

- Props: `{ cif: string, profileId: string }`.
- `GET /forecast/{cif}` → lịch sử + dự báo hàng ngày.
- `GET /profiles/{profileId}/analysis` → NCF kế hoạch từ profile.

**Biểu đồ Recharts (ComposedChart):**
- **Trục X:** tuần (Monday của mỗi tuần) — 52 tuần lịch sử + ~12 tuần dự báo.
- **Line "Thực tế"** (indigo solid): weekly sum của history, `connectNulls=false`.
- **Line "Dự báo"** (indigo dashed): weekly sum của forecast, `connectNulls=false`.
- **Area "Khoảng tin cậy"**: [lower, upper] dải Prophet, gradient indigo.
- **ReferenceLine y=0**: đường 0.
- **ReferenceLine x=splitDate**: "Hiện tại" — ranh giới history/forecast.
- **ReferenceLine y=weeklyTarget**: "Kế hoạch" — NCF/4.33 từ profile.

**Khoảng trống tự nhiên** giữa history và forecast: `actual=null` ở tuần forecast và `yhat=null` ở tuần history → `connectNulls=false` tạo visual gap. Không có duplicate week keys nhờ: forecast skip tuần `<= lastHistWeek`.

**Summary:** next_30_net và next_90_net hiển thị dạng số ở header card.

### 5.4 TransactionImport

- Drag & drop hoặc click để chọn file `.csv`, `.xlsx`, `.xls`.
- Upload bằng `FormData` + raw `fetch` (không dùng `apiFetch` vì multipart).
- Sau khi extract: hiện tóm tắt (avg income, avg expense, avg net).
- "Xem lại & Lưu hồ sơ →" → callback `onExtracted(suggestedProfile, cif?)`.

### 5.5 ProfileBuilder

- Controlled form với sections: Thu nhập, Chi tiêu, Khoản nợ, Tài sản, Quỹ khẩn cấp, Mục tiêu.
- `mode="create"` → `POST /profiles` → trả về `{ id }` → set active.
- `mode="update"` → `PUT /profiles/{id}`.
- `initialProfile` null → form trống; không-null → pre-fill.
- Money inputs: hiển thị formatted VND, parse về `int` khi submit.

---

## 6. State Management

| State | Nơi lưu | Mô tả |
|-------|---------|-------|
| `token` | `localStorage["bnpl.token"]` | Auth token |
| `activeProfileId` | `localStorage["bnpl.activeProfileId"]` | Profile đang dùng |
| `importedCif` | React state (Shell) | CIF để hiện ForecastSection |
| `savedProfile` | React state (Shell) | Profile object cho UpdateWizard |
| `setupStep` | React state | "import" \| "review" |
| `updating` | React state | Đang ở UpdateWizard hay không |

---

## 7. API Client

```typescript
// client.ts
apiFetch<T>(path, init?): Promise<T>
  // prefix /api, JSON headers, throws ApiError{status, detail} on non-2xx

// endpoints.ts — key functions
createProfile(body: ProfileIn): Promise<{ id: string }>
updateProfile(body: ProfileIn): Promise<{ id: string }>
getProfile(id: string): Promise<ProfileIn>
getAnalysis(id: string): Promise<MetricsOut>
getAlerts(id: string): Promise<AlertsOut>
evaluatePurchase(body: EvaluateIn): Promise<EvaluateOut>
getForecast(cif: string): Promise<ForecastOut>
extractProfile(file: File): Promise<ExtractResponse>  // raw fetch + FormData
```

---

## 8. Error Handling

- `ApiError(status, detail)` từ `apiFetch` trên non-2xx.
- **404 profile** trong HealthSidebar → `onProfileNotFound()` → `resetProfile()` → xoá `localStorage` → quay Onboarding.
- Network error → `ErrorBanner` "Không kết nối được máy chủ".
- Upload error → `ErrorBanner` với detail từ backend.

---

## 9. Testing

**Unit (Vitest):** `money.ts`, `bands.ts`, `client.ts`, `profileForm.ts` — pure functions.

**Component (RTL):**
- `LoginScreen` — submit credentials, lưu token.
- `ProfileBuilder` — submit happy path.
- `AnalysisDashboard` — render metrics từ mocked API.
- `PurchaseEvaluator` — render phương án với đúng nhãn tiếng Việt.
- `App` — login screen khi chưa có token; setup wizard khi đã login; import step mặc định.

Tổng: **26 tests, 12 test files**, tất cả pass.

---

## 10. Ngoài phạm vi MVP

- `importedCif` không persist vào localStorage → ForecastSection mất sau reload (chỉ hoạt động trong session).
- Giao dịch upload không lưu lại phía backend cho Prophet — chỉ demo CIF `10001234` có forecast data.
- Charts mobile responsive chưa tối ưu.
