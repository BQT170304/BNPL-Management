# BNPL Assistant — Design Spec (As-Built)

**Version:** 2.0
**Date cập nhật:** 2026-06-06
**Trạng thái:** Đã triển khai — tài liệu phản ánh code hiện tại

---

## 1. Mục đích

Hệ thống tư vấn tài chính cá nhân ("BNPL Assistant"). Mỗi tài khoản có **một hồ sơ tài chính duy nhất**, được tạo bằng cách tải lên file giao dịch ngân hàng (CSV/XLSX). Hệ thống:

1. Trích xuất tự động thu nhập, chi tiêu theo danh mục, khoản nợ từ lịch sử giao dịch.
2. Tính toán các chỉ số sức khoẻ tài chính (NCF, DTI, EFR, PGRS).
3. Đối với mỗi giao dịch mua sắm được đề xuất, tạo và xếp hạng các phương án thanh toán.
4. Dự báo dòng tiền bằng Prophet dựa trên lịch sử giao dịch.

---

## 2. Kiến trúc

**Clean Architecture trong Modular Monolith.** Một FastAPI app. Mỗi module là một bounded context với 4 layer; dependencies chỉ hướng vào trong.

```
domain          entities, value objects, formulas — không I/O
  ↑
application     use cases, DTOs, ports (interfaces)
  ↑
infrastructure  SQLAlchemy repositories, CSV reader, Prophet adapter
  ↑
api             FastAPI routers + Pydantic schemas
```

### 2.1 Cấu trúc thư mục thực tế

```
app/
  main.py                        # app factory, startup events, DI wiring, demo seeder
  core/
    config.py                    # pydantic-settings (env-driven)
    database.py                  # async SQLAlchemy engine/session, Base
    money.py                     # VND = int
    errors.py                    # domain exceptions → HTTP handlers
    clock.py                     # Clock port (today()) — injectable for tests
  dependencies.py                # DI: repo, services, forecaster
  modules/
    profiles/
      domain/       entities.py, value_objects.py
      application/  ports.py, transaction_extractor.py
      infrastructure/ memory_repository.py, sqlalchemy_repository.py
      api/          router.py, schemas.py, mappers.py
    goals/
      domain/       entities.py
    analysis/
      domain/       formulas.py, thresholds.py, allocation.py, results.py
      application/  services.py
      api/          router.py, schemas.py
    advisory/
      domain/       options.py, subscores.py, scoring.py
      application/  dto.py, ports.py, services.py, simulator.py
      api/          router.py, schemas.py
    explanation/
      infrastructure/ deterministic_scorer.py, bedrock_scorer.py
    ingestion/
      application/  ports.py, services.py
      infrastructure/ csv_source.py
      api/          router.py, schemas.py
    forecasting/
      domain/       models.py, daily_net.py
      application/  service.py, ports.py
      infrastructure/ prophet_forecaster.py, naive_forecaster.py,
                      csv_transaction_source.py, matplotlib_chart.py
      api/          router.py, schemas.py
data/
  demo_transactions_10001234.csv  # 18 tháng giao dịch mẫu Jan 2025–Jun 2026
  transactions_labeled.csv        # bản có nhãn danh mục
tests/
  unit/
  integration/
.env
requirements.txt
```

---

## 3. Persistence

**SQLite** (default) — lưu hồ sơ vào file `bnpl.db`. Hỗ trợ thêm Postgres qua cùng port `ProfileRepository`.

**`.env`:**
```
PERSISTENCE=sqlite
SQLITE_PATH=bnpl.db
CORS_ORIGINS=http://localhost:5173,http://localhost:5174
```

**Khởi động app** (`main.py` startup event):
1. `Base.metadata.create_all` — tạo bảng SQLite nếu chưa có.
2. `_seed_demo_profile()` — nếu `"demo-profile"` chưa tồn tại, tạo hồ sơ mẫu (lập trình viên 27 tuổi, lương 19M/tháng).

---

## 4. Domain model

### 4.1 Profiles

- **FinancialProfile** — root aggregate. Một account = một profile.
  - **Income:** `salary`, `secondary`, `avg_bonus_monthly`, `passive`.
  - `total_income` = sum (computed).
- **Expense** (many) — `category`, `amount`, `classification ∈ {FIXED, SEMI_FIXED, DISCRETIONARY}`.
- **Debt** (many) — `name`, `monthly_payment` (required), `balance` (nullable), `apr`, `months_remaining` (nullable), `debt_type ∈ {REVOLVING, INSTALLMENT, SECURED}`.
- **Asset** (many) — `type`, `value`, `liquidity`.
- **EmergencyFund** — `balance` (số tiền hiện đang có, **nhập tay**, không suy luận từ giao dịch).
- **RiskTolerance** — `LOW | MEDIUM | HIGH`.

### 4.2 Goals

- **Goal** (many per profile) — `name`, `target_amount`, `deadline`, `priority ∈ {LOW, MEDIUM, HIGH, VERY_HIGH}`, `savings_allocated`.
- Hoàn toàn **do user nhập tay** — không trích xuất từ giao dịch.

---

## 5. Transaction Extractor (`profiles/application/transaction_extractor.py`)

Chuyển đổi file giao dịch ngân hàng → hồ sơ tài chính sơ bộ.

### 5.1 Định dạng file đầu vào

| Cột | Mô tả |
|-----|-------|
| `CIF_NO` | Mã khách hàng (tuỳ chọn) |
| `NOTE` | Nội dung giao dịch (tiếng Việt không dấu) |
| `TRAN_DATE` | Ngày giao dịch |
| `AMOUNT` | Số tiền (dương = tiền vào, âm = tiền ra) |

Hỗ trợ: CSV, XLSX, XLS. Deduplication theo `(NOTE, TRAN_DATE, AMOUNT)`.

### 5.2 Phân loại giao dịch (keyword matching)

| Danh mục | Từ khoá đặc trưng |
|----------|------------------|
| **Thu nhập lương** | luong, tra luong, phu cap, tro cap, thu lao |
| **Thu nhập thưởng** | thuong, bonus, thuong kpi, thuong tet |
| **Thu nhập thụ động** | lai suat, lai tiet kiem, cho thue |
| **Thu nhập phụ** | thu lao freelance, lam them, part time |
| **Nhà ở** | tien nha, tien phong, nha tro, thue nha |
| **Điện/nước/mạng** | tien dien, tien nuoc, tien mang, internet, wifi |
| **Ăn uống** | an trua, an sang, do an, bun bo, pho, cafe |
| **Đi lại** | do xang, grab, taxi, ve tau, bus |
| **Khoản nợ** | tra gop, tra no, thanh toan the, tra vay |
| **Y tế** | thuoc, benh vien, kham benh |
| **Học tập** | hoc phi, hoc them, khoa hoc |
| **Giải trí** | phim, karaoke, du lich, the gym |
| **Mua sắm** | lazada, shopee, mua online, dat hang |

### 5.3 Logic tổng hợp

- Nhóm giao dịch theo tháng, bỏ tháng có < 5 giao dịch (partial month).
- Tính trung bình các tháng đủ dữ liệu.
- Bonus chia 3 (vì thường trả theo quý).
- Thu không phân loại được tính 30% vào secondary (conservative, vì có thể là chuyển khoản nội bộ).

### 5.4 Những gì **không** trích xuất — user tự nhập

| Trường | Lý do |
|--------|-------|
| `emergency_fund` | Giao dịch tiết kiệm không phân biệt được quỹ khẩn cấp vs. mục tiêu khác |
| `goals` | Mục tiêu tài chính là do user đặt ra, không có trong giao dịch |
| Chi tiết khoản nợ (balance, apr, months_remaining) | Chỉ thấy số tiền trả hàng tháng |

---

## 6. Analysis Engine (`analysis/domain/formulas.py`)

Tất cả là pure functions.

| Chỉ số | Công thức | Ý nghĩa |
|--------|-----------|---------|
| `net_cash_flow` (NCF) | income − expense − debt_payment | Tiền còn lại / tháng |
| `dti` | debt_payment / income × 100 | Tỷ lệ nợ |
| `saving_rate` | NCF / income × 100 | Tỷ lệ tiết kiệm |
| `efr` | emergency_fund / essential_expense | Quỹ dự phòng (số tháng) |
| `gat` | goal_gap / monthly_allocated | Thời gian đạt mục tiêu (tháng) |
| `grs` | min(100, goal_delay / months_remaining × 100) | Rủi ro mục tiêu đơn |
| `pgrs` | Σ(grs·weight) / Σ(weight) | Rủi ro danh mục mục tiêu |

**DTI bands:** `<20` SAFE · `20–35` ACCEPTABLE · `35–40` WARNING · `>40` DANGER.

**Allocation:** `PriorityWeightedAllocation` (default) — chia NCF theo `priority_weight` của từng goal.

---

## 7. Alerts (`profiles/{id}/alerts`)

Tự động sinh cảnh báo dựa trên chỉ số phân tích:

| Code | Level | Trigger |
|------|-------|---------|
| `NEGATIVE_NCF` | CRITICAL | NCF < 0 |
| `HIGH_DTI` | WARNING/CRITICAL | DTI > 35% / > 40% |
| `LOW_EFR` | WARNING | EFR < 3 tháng |
| `GOALS_AT_RISK` | WARNING | PGRS > 50 |
| `GOAL_UNREACHABLE_{id}` | WARNING | GAT > months_remaining |

Response: `{ profile_id, alerts: [...], has_critical: bool }`.

---

## 8. Advisory (`/advisory/evaluate`, `/advisory/simulate`)

### 8.1 Tạo phương án thanh toán

Cho purchase amount `P`: pay-in-full, trả góp 3/6/12 tháng (hoặc danh sách tuỳ chỉnh). `monthly_payment = ceil(P / n)` với APR mặc định 0%.

### 8.2 Sub-scores (deterministic)

1. **S_CashFlow** — payment vs. NCF: ≤50% NCF → 100 · 50–80% → 60 · 80–100% → 20 · >NCF → 0.
2. **S_Goal** — `100 − min(100, ΔPGRS × 3)`.
3. **S_EFR** — EFR sau quyết định: ≥6 → 100 · 3–6 → 70 · 1–3 → 30 · <1 → 0.
4. **S_DTI** — DTI mới: <20 → 100 · 20–35 → 70 · 35–40 → 40 · >40 → 0.

### 8.3 Risk scoring

- **BedrockScorer** (primary): LLM AWS Bedrock, JSON schema nghiêm ngặt. Risk score 0–100 (0 = an toàn nhất).
- **DeterministicScorer** (fallback): `weighted_score = 0.35·S_CF + 0.35·S_Goal + 0.20·S_EFR + 0.10·S_DTI`; `risk_score = 100 − weighted_score`.

---

## 9. Forecasting (`/forecast/{cif}`)

Dự báo dòng tiền từ lịch sử giao dịch của một CIF.

**Data source:** `data/transactions_labeled.csv` — mỗi dòng là một giao dịch ngày với `CIF_NO, NOTE, TRAN_DATE, AMOUNT`. Demo CIF `10001234` có 18 tháng dữ liệu (Jan 2025 – Jun 2026).

**Pipeline:**
1. `CsvTransactionSource.history(cif)` → list `HistoryPoint(ds: date, y: float)` (daily net cash flow).
2. `ProphetForecaster.forecast(series, horizon=90)` → 90 ngày dự báo.
3. Response: `{ cif, next_30_net, next_90_net, history: [...], forecast: [...{ds, yhat, lower, upper}] }`.

**Prophet config:** weekly seasonality, additive mode, `changepoint_prior_scale=0.05`, thêm monthly seasonality (fourier_order=5).

---

## 10. API Surface

| Method | Path | Mô tả |
|--------|------|-------|
| POST | `/auth/login` | Đăng nhập, trả về Bearer token |
| GET | `/demo-profile-id` | ID của hồ sơ demo |
| POST | `/profiles` | Tạo hồ sơ mới |
| GET | `/profiles/{id}` | Lấy hồ sơ |
| PUT | `/profiles/{id}` | Cập nhật hồ sơ |
| GET | `/profiles/{id}/analysis` | Chỉ số sức khoẻ tài chính |
| GET | `/profiles/{id}/alerts` | Cảnh báo tự động |
| **POST** | **`/profiles/extract`** | **Upload file giao dịch → trích xuất hồ sơ sơ bộ** |
| POST | `/advisory/evaluate` | Đánh giá mua sắm |
| POST | `/advisory/explain` | Giải thích tự nhiên (LLM) |
| POST | `/advisory/simulate` | Mô phỏng kịch bản |
| GET | `/forecast/{cif}` | Dự báo dòng tiền Prophet |
| GET | `/ingestion/cifs` | Danh sách CIF (legacy) |

### POST `/profiles/extract` — file upload

**Request:** `multipart/form-data`, field `file` (CSV hoặc XLSX).

**Response:**
```json
{
  "suggested_profile": { ...ProfileIn },
  "summary": {
    "months_analyzed": 18,
    "avg_monthly_income": 23500000,
    "avg_monthly_expense": 16800000,
    "avg_monthly_net": 6700000,
    "cif": "10001234"
  }
}
```

**Quy tắc trích xuất:** chỉ điền những gì đọc được trực tiếp từ giao dịch. `emergency_fund = 0`, `goals = []` — user tự nhập sau.

---

## 11. Authentication

Bearer token đơn giản (demo):
- Username: `nguyenvana` / Password: `123456` → token `demo-token-bnpl`.
- Tất cả endpoints (trừ `/health`, `/auth/login`) yêu cầu `Authorization: Bearer <token>`.

---

## 12. Config

| Biến | Default | Mô tả |
|------|---------|-------|
| `PERSISTENCE` | `sqlite` | `memory \| sqlite \| postgres` |
| `SQLITE_PATH` | `bnpl.db` | Đường dẫn file SQLite |
| `DATABASE_URL` | — | Postgres URL (khi PERSISTENCE=postgres) |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated |
| `BEDROCK_ENABLED` | `false` | Bật AWS Bedrock scorer |
| `FORECAST_HORIZON` | `90` | Số ngày dự báo Prophet |
| `FORECAST_CSV_PATH` | `data/transactions_labeled.csv` | File giao dịch cho forecasting |

---

## 13. Ngoài phạm vi MVP

Multi-user auth, lưu trữ giao dịch upload cho từng user (hiện chỉ demo CIF có dữ liệu forecast), scheduled reminders, deployment CI/CD.
