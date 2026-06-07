# BNPL Smart Advisory — Competition Plan

## Tổng Quan

Dự án BNPL Smart Advisory là một **plugin tư vấn tài chính thông minh** tích hợp vào ứng dụng ngân hàng, giúp người dùng đưa ra quyết định thanh toán tối ưu khi mua sắm. Hệ thống phân tích sức khỏe tài chính real-time, so sánh các phương án thanh toán (trả thẳng, trả góp, thẻ tín dụng, BNPL), và đưa ra khuyến nghị cá nhân hóa dựa trên scoring engine + AI.

Plan này bao gồm **2 track song song**:
1. **Track 1**: Chuẩn bị tài liệu thuyết trình (Solution Summary + Slide Deck)
2. **Track 2**: Redesign & Rebuild demo (Frontend + Backend adjustments)

---

## User Review Required

> [!IMPORTANT]
> **Định vị sản phẩm**: Tôi đề xuất định vị là **"Smart Payment Advisory Plugin"** — một module tích hợp vào mobile banking app của ngân hàng (không phải app standalone). Điều này thể hiện tính khả thi cao hơn vì:
> - Ngân hàng đã có sẵn dữ liệu khách hàng (thu nhập, chi tiêu, nợ)
> - Không cần khách hàng cài thêm app mới
> - Tận dụng được hạ tầng bảo mật sẵn có
> - Phù hợp xu hướng Open Banking và embedded finance
>
> **Bạn có đồng ý với hướng này không?**

> [!IMPORTANT]
> **Scope Demo**: Với thời gian có hạn, tôi đề xuất ưu tiên các chức năng sau cho demo:
> 1. ✅ Smart Payment Advisor (core feature) — so sánh phương án thanh toán
> 2. ✅ Financial Health Dashboard — dashboard sức khỏe tài chính
> 3. ✅ Cash Flow Forecast — dự báo dòng tiền
> 4. ✅ What-if Simulation — mô phỏng tác động
> 5. ⬜ Goal Tracking (simplified)
> 6. ⬜ Smart Alerts
>
> **Bạn muốn thêm/bớt chức năng nào?**

> [!WARNING]
> **Video Demo trong slide**: Bạn cần quay video demo riêng hay dùng live demo? Tôi recommend quay video 2-3 phút để đảm bảo smooth và không gặp lỗi kỹ thuật khi trình bày.

---

## Open Questions

1. **Tên cuộc thi cụ thể là gì?** — Để customize slide phù hợp với tiêu chí chấm điểm
2. **Đối tượng giám khảo** — Có cả giám khảo kỹ thuật và nghiệp vụ, hay chủ yếu nghiệp vụ?
3. **Ngân hàng sponsor** — Cuộc thi có ngân hàng cụ thể tổ chức không? Nếu có thì cần align sản phẩm với chiến lược của ngân hàng đó
4. **Thời gian còn lại** — Bao lâu nữa đến ngày trình bày? Để ưu tiên task hợp lý
5. **Có cần hỗ trợ tiếng Anh** — Slide/thuyết trình bằng tiếng Việt hay tiếng Anh?

---

# TRACK 1: TÀI LIỆU THUYẾT TRÌNH

## 1.1 Solution Summary Document

Sẽ tạo file `solution_summary.md` bao gồm:

### Mô tả bài toán
- Pain point: Người tiêu dùng VN ngày càng có nhiều lựa chọn thanh toán (cash, credit card, installment, BNPL) nhưng **không có công cụ nào giúp so sánh và đưa ra quyết định phù hợp** với tình hình tài chính cá nhân
- Hệ quả: 47% người dùng BNPL tại VN gặp khó khăn trong quản lý nợ (nguồn: SBV 2025), tỷ lệ nợ xấu tăng, ngân hàng chịu rủi ro

### Giải pháp
- **Smart Payment Advisory Engine**: Scoring engine đa chiều (6 chỉ số tài chính) + AI để xếp hạng phương án thanh toán
- **Tích hợp như plugin** vào mobile banking app — tận dụng data sẵn có của ngân hàng
- **Dual-engine**: Deterministic scoring (minh bạch, audit được) + LLM scoring (AWS Bedrock) cho giải thích tự nhiên

### Kiến trúc & Luồng hoạt động
```
[Mobile Banking App]
       ↓
[Smart Payment Plugin UI] ← React/TypeScript (mobile-first)
       ↓
[API Gateway / Backend] ← FastAPI
       ↓
┌──────────┬──────────────┬─────────────┬──────────────┐
│ Analysis │  Advisory    │ Forecasting │ Simulation   │
│ Engine   │  Engine      │ (Prophet)   │ Engine       │
│ (6 KPIs) │ (Risk Score) │             │ (What-if)    │
└──────────┴──────────────┴─────────────┴──────────────┘
       ↓                        ↓
[Deterministic Scorer]    [AWS Bedrock LLM]
(weighted formula)        (explainable AI)
```

### Công nghệ & Tính khả thi
| Component | Technology | Lý do chọn |
|-----------|-----------|------------|
| Backend | FastAPI (Python) | High performance, async, OpenAPI auto-docs |
| Scoring | Deterministic + AWS Bedrock | Minh bạch + AI, có fallback |
| Forecasting | Prophet / Naive | Industry-standard time series |
| Frontend | React + TypeScript | Component-based, type-safe |
| Database | PostgreSQL | Production-grade, ngân hàng quen dùng |

### Tính pháp lý
- Không thu thập data mới — dùng data ngân hàng đã có (tuân thủ PDPA)
- Scoring engine minh bạch, có thể audit (comply với SBV regulations)
- Không phải sản phẩm tín dụng mới — chỉ là **công cụ tư vấn**
- Phù hợp Nghị định 94/2025/NĐ-CP về fintech sandbox

### Tác động kỳ vọng
- **Cho ngân hàng**: Tăng engagement trên app (+15-20%), giảm tỷ lệ nợ xấu BNPL (dự kiến -10-15%), tăng cross-sell sản phẩm tín dụng
- **Cho khách hàng**: Ra quyết định tài chính thông minh hơn, giảm rủi ro over-debt, được tư vấn cá nhân hóa
- **Cho thị trường**: Thúc đẩy "responsible lending", nâng cao financial literacy

---

## 1.2 Slide Deck Outline (8-10 phút)

### Slide 1: Title (15s)
**"Smart Payment Advisor — Trợ lý thanh toán thông minh"**
- Tagline: *"Mua sắm thông minh, thanh toán tối ưu"*
- Team name, logo

### Slide 2: The Story — Hook (45s)
**Storytelling mở đầu:**
> *"Minh, 28 tuổi, nhân viên văn phòng, thu nhập 18 triệu/tháng. Minh muốn mua một chiếc laptop 25 triệu. Trước mặt Minh có 4 lựa chọn: trả thẳng, quẹt thẻ tín dụng, trả góp 12 tháng, hoặc BNPL chia 4 lần. Minh không biết chọn phương án nào phù hợp nhất với tình hình tài chính hiện tại..."*

- Visual: Hình minh họa người đứng trước 4 con đường chia rẽ
- Key message: **Đây là bài toán 26 triệu người tiêu dùng VN đang đối mặt mỗi ngày**

### Slide 3: The Problem — Pain Points (45s)
- **Số liệu**: 47% người dùng BNPL gặp khó khăn quản lý nợ
- **Vấn đề 1**: Không có công cụ so sánh phương án thanh toán dựa trên tình hình tài chính cá nhân
- **Vấn đề 2**: Ngân hàng chịu rủi ro nợ xấu khi khách hàng chọn sai phương án
- **Vấn đề 3**: Các app BNPL hiện tại (MoMo, Fundiin, Kredivo) chỉ push bán hàng, không tư vấn

### Slide 4: Our Solution — Overview (60s)
**"Smart Payment Advisor"** — Plugin tích hợp vào mobile banking app
- Phân tích sức khỏe tài chính real-time (6 chỉ số)
- So sánh & xếp hạng phương án thanh toán tối ưu
- AI giải thích dễ hiểu tại sao nên/không nên chọn
- Dự báo dòng tiền & mô phỏng tác động

*Diagram kiến trúc đơn giản*

### Slide 5: Differentiators — Tại sao chúng tôi khác biệt (45s)
| Đối thủ (BNPL apps) | Chúng tôi |
|---|---|
| Push khách mua nhiều hơn | Tư vấn khách mua **đúng cách** |
| Chỉ cung cấp 1 phương án (BNPL) | So sánh **tất cả phương án** |
| Không biết tình hình tài chính khách | **Phân tích toàn diện** 6 chỉ số tài chính |
| Black-box scoring | **Minh bạch**, giải thích được |
| Standalone app riêng | **Plugin** tích hợp ngân hàng — zero friction |

### Slide 6: For the Bank — Giá trị cho ngân hàng (30s)
- 📈 **Tăng engagement**: Khách mở app thường xuyên hơn (+15-20%)
- 🛡️ **Giảm nợ xấu**: Khách chọn phương án phù hợp khả năng (-10-15% bad debt)
- 💰 **Tăng revenue**: Cross-sell sản phẩm (trả góp, thẻ tín dụng)
- 🏆 **Competitive advantage**: Đi đầu xu hướng "responsible banking"
- ⚖️ **Tuân thủ pháp luật**: Comply SBV, PDPA, sandbox fintech

### Slide 7: Technical Deep-dive — Scoring Engine (60s)
**Dual-Engine Architecture:**

**Engine 1: Deterministic Scorer (6 chỉ số)**
- NCF (Net Cash Flow) — Dòng tiền ròng sau mua
- DTI (Debt-to-Income) — Tỷ lệ nợ/thu nhập
- Saving Rate — Tỷ lệ tiết kiệm
- EFR (Emergency Fund Ratio) — Tỷ lệ quỹ khẩn cấp
- GRS (Goal Readiness Score) — Mức sẵn sàng đạt mục tiêu
- PGRS (Portfolio GRS) — Điểm tổng hợp mục tiêu

**Formula**: `risk = 0.35×DTI + 0.25×NCF + 0.20×Saving + 0.10×EFR + 0.10×Goal`
*(Trọng số dựa trên nghiên cứu Basel III & consumer credit risk best practices)*

**Engine 2: LLM Scorer (AWS Bedrock)**
- Claude AI phân tích context tài chính
- Sinh giải thích bằng ngôn ngữ tự nhiên
- Fallback tự động sang deterministic nếu LLM fail

### Slide 8: Technical Deep-dive — Dự báo & Mô phỏng (30s)
- **Cash Flow Forecasting**: Prophet (Facebook) time-series — dự báo 30/90 ngày
- **What-if Simulation**: Mô phỏng trước/sau khi mua — thấy rõ tác động
- **Smart Alerts**: Cảnh báo khi DTI vượt ngưỡng, NCF âm

### Slide 9: Demo Video (2-3 phút)
Luồng demo:
1. Mở banking app → Chọn "Smart Payment Advisor"
2. Dashboard sức khỏe tài chính hiện ra (đã có data từ ngân hàng)
3. Nhập thông tin mua hàng (laptop 25 triệu)
4. Hệ thống so sánh 4 phương án → Khuyến nghị "Trả góp 6 tháng" là tối ưu
5. Xem giải thích chi tiết tại sao
6. Xem dự báo dòng tiền & mô phỏng tác động
7. Quay lại story: *"Minh đã chọn đúng, và 6 tháng sau vẫn đạt mục tiêu tích lũy"*

### Slide 10: Roadmap & Kết luận (30s)
- **Phase 1** (hiện tại): Advisory engine + Dashboard
- **Phase 2**: Tích hợp Open Banking API, multi-bank
- **Phase 3**: Merchant integration, personalized offers
- **Call to action**: *"Smart Payment Advisor — Giúp khách hàng mua sắm thông minh, giúp ngân hàng tăng trưởng bền vững"*

---

# TRACK 2: REDESIGN & REBUILD DEMO

## 2.1 Product Definition

### Concept
**"Smart Payment Advisor"** — Một chức năng mới trong mobile banking app. Trên web demo, chúng ta sẽ render giao diện trong một **mobile frame** (375×812px — iPhone viewport) để tạo cảm giác đây là một tính năng thực sự trong app ngân hàng.

### Trang & Luồng chính
```
[Splash/Loading] → [Home Dashboard] → [Purchase Input] → [Comparison Results] → [Detail View]
                         ↕                                        ↕
                  [Financial Health]                    [Forecast & Simulation]
```

### Các trang cụ thể:

| # | Trang | Mô tả | Ưu tiên |
|---|-------|-------|---------|
| 1 | **Home Dashboard** | Tổng quan sức khỏe tài chính + Quick action | P0 |
| 2 | **Purchase Advisor** | Nhập thông tin mua hàng | P0 |
| 3 | **Comparison Results** | So sánh & xếp hạng phương án | P0 |
| 4 | **Option Detail** | Chi tiết 1 phương án + giải thích AI | P0 |
| 5 | **Financial Health** | Dashboard chi tiết 6 chỉ số | P1 |
| 6 | **Cash Flow Forecast** | Biểu đồ dự báo dòng tiền | P1 |
| 7 | **Simulation** | What-if comparison before/after | P1 |

---

## 2.2 Design System & Theme

### Brand Identity
- **App Name**: Smart Payment Advisor (SPA)
- **Tagline**: "Thanh toán thông minh, tài chính vững vàng"

### Color Palette

```css
/* Primary — Deep Blue (trust, banking) */
--primary-50: #EFF6FF;
--primary-100: #DBEAFE;
--primary-200: #BFDBFE;
--primary-500: #3B82F6;
--primary-600: #2563EB;
--primary-700: #1D4ED8;
--primary-900: #1E3A5F;

/* Accent — Emerald Green (growth, positive) */
--accent-50: #ECFDF5;
--accent-500: #10B981;
--accent-600: #059669;

/* Semantic Colors */
--success: #22C55E;
--warning: #F59E0B;
--danger: #EF4444;
--info: #06B6D4;

/* Neutral — Cool Gray */
--gray-50: #F8FAFC;
--gray-100: #F1F5F9;
--gray-200: #E2E8F0;
--gray-400: #94A3B8;
--gray-600: #475569;
--gray-800: #1E293B;
--gray-900: #0F172A;

/* Background */
--bg-primary: #F8FAFC;     /* Light mode */
--bg-card: #FFFFFF;
--bg-dark: #0F172A;        /* Dark sections */

/* Gradients */
--gradient-primary: linear-gradient(135deg, #1D4ED8, #3B82F6);
--gradient-hero: linear-gradient(180deg, #1E3A5F, #2563EB);
--gradient-success: linear-gradient(135deg, #059669, #10B981);
--gradient-danger: linear-gradient(135deg, #DC2626, #EF4444);
```

### Typography
```css
/* Font Family */
--font-primary: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;

/* Scale */
--text-xs: 0.75rem;    /* 12px — caption */
--text-sm: 0.875rem;   /* 14px — body small */
--text-base: 1rem;     /* 16px — body */
--text-lg: 1.125rem;   /* 18px — subtitle */
--text-xl: 1.25rem;    /* 20px — heading small */
--text-2xl: 1.5rem;    /* 24px — heading */
--text-3xl: 1.875rem;  /* 30px — heading large */

/* Weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### Spacing & Layout (Mobile-first)
```css
/* Container */
--mobile-width: 375px;
--mobile-height: 812px;
--safe-area-top: 44px;     /* Status bar */
--safe-area-bottom: 34px;  /* Home indicator */
--nav-height: 56px;        /* Bottom nav */

/* Spacing scale */
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;

/* Border radius */
--radius-sm: 8px;
--radius-md: 12px;
--radius-lg: 16px;
--radius-xl: 20px;
--radius-full: 9999px;
```

### Component Specs

#### Cards
- Background: white, `border-radius: 16px`
- Shadow: `0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06)`
- Padding: 16px
- Hover/Active: subtle scale transform (0.98)

#### Buttons
- **Primary**: Gradient background (primary), white text, rounded-full, height 48px
- **Secondary**: White bg, primary border, primary text
- **Ghost**: Transparent, primary text
- Disabled: opacity 0.5
- Tap animation: scale(0.96)

#### Bottom Navigation Bar
- 5 tabs: Home | Advisor | Health | Forecast | Profile
- Active tab: primary color icon + label
- Inactive: gray-400
- Background: white with top border
- Height: 56px + safe-area-bottom

#### Score Gauge (Risk Score)
- Circular progress ring (SVG)
- Color: green (0-30), amber (31-60), red (61-100)
- Center: score number + label
- Smooth animation on load

#### Metric Cards (Health Dashboard)
- Icon + Label + Value
- Progress bar underneath
- Color-coded status dot
- Tooltip with explanation on tap

---

## 2.3 Page-by-Page UI Specification

### Page 1: Home Dashboard
**Layout:**
```
┌──────────────────────────┐
│ [Status Bar]             │
│                          │
│  Chào Minh 👋            │
│  Sức khỏe tài chính      │
│                          │
│  ┌────────────────────┐  │
│  │  Overall Score: 72  │  │
│  │  [Circular Gauge]   │  │
│  │  Khá tốt ✓          │  │
│  └────────────────────┘  │
│                          │
│  ┌──────┐ ┌──────┐      │
│  │ NCF  │ │ DTI  │      │
│  │ 5.2M │ │ 28%  │      │
│  │  ✅   │ │  ✅   │      │
│  └──────┘ └──────┘      │
│  ┌──────┐ ┌──────┐      │
│  │Save% │ │ EFR  │      │
│  │ 22%  │ │ 4.1  │      │
│  │  ✅   │ │  ⚠️   │      │
│  └──────┘ └──────┘      │
│                          │
│  ┌────────────────────┐  │
│  │ 🛍️ Tư vấn mua sắm  │  │
│  │ Bạn đang cân nhắc  │  │
│  │ mua gì?    [Bắt đầu]│  │
│  └────────────────────┘  │
│                          │
│  📊 Dòng tiền 30 ngày   │
│  [Mini line chart]       │
│  Dự kiến: +3.2M ↗       │
│                          │
│ [Home][Advisor][Health]  │
│ [Forecast][Profile]      │
└──────────────────────────┘
```

**Interactions:**
- Tap gauge → Navigate to Financial Health detail
- Tap metric card → Show tooltip/detail
- Tap "Bắt đầu" → Navigate to Purchase Advisor
- Tap mini chart → Navigate to Forecast
- Bottom nav for page switching

### Page 2: Purchase Advisor (Input)
**Layout:**
```
┌──────────────────────────┐
│ ← Tư vấn thanh toán      │
│                          │
│  Bạn muốn mua gì?       │
│                          │
│  ┌────────────────────┐  │
│  │ 💻 Tên sản phẩm    │  │
│  │ [Laptop MacBook Air]│  │
│  └────────────────────┘  │
│                          │
│  ┌────────────────────┐  │
│  │ 💰 Số tiền          │  │
│  │ [25,000,000 ₫]      │  │
│  └────────────────────┘  │
│                          │
│  ┌────────────────────┐  │
│  │ 📂 Danh mục         │  │
│  │ [Công nghệ     ▼]  │  │
│  └────────────────────┘  │
│                          │
│  Chọn phương án so sánh  │
│                          │
│  ☑️ Trả thẳng            │
│  ☑️ Thẻ tín dụng         │
│  ☑️ Trả góp              │
│  ☑️ BNPL (Mua trước...)  │
│                          │
│  [Cấu hình chi tiết ▼]  │
│  (expandable: lãi suất,  │
│   kỳ hạn cho từng option)│
│                          │
│  ┌────────────────────┐  │
│  │  🔍 Phân tích ngay  │  │
│  └────────────────────┘  │
│                          │
│ [Home][Advisor][Health]  │
└──────────────────────────┘
```

**Interactions:**
- Dropdown cho category với icons
- Checkbox toggle cho mỗi phương án
- Expandable section cho cấu hình chi tiết (lãi suất, kỳ hạn)
- Loading animation khi gọi API
- Haptic-like animation khi tap "Phân tích"

### Page 3: Comparison Results
**Layout:**
```
┌──────────────────────────┐
│ ← Kết quả phân tích      │
│                          │
│  Laptop MacBook Air      │
│  25,000,000 ₫            │
│                          │
│  ⭐ KHUYẾN NGHỊ          │
│  ┌────────────────────┐  │
│  │ 🥇 Trả góp 6 tháng │  │
│  │                    │  │
│  │ Risk: [===---] 32  │  │
│  │ Tổng chi phí:      │  │
│  │   25,750,000 ₫     │  │
│  │ Hàng tháng:        │  │
│  │   4,291,667 ₫      │  │
│  │ Tác động NCF: -17% │  │
│  │                    │  │
│  │ [Xem chi tiết →]   │  │
│  └────────────────────┘  │
│                          │
│  ┌────────────────────┐  │
│  │ 🥈 BNPL 4 kỳ       │  │
│  │ Risk: [====--] 45  │  │
│  │ 25,000,000 ₫       │  │
│  │ [Xem chi tiết →]   │  │
│  └────────────────────┘  │
│                          │
│  ┌────────────────────┐  │
│  │ 🥉 Thẻ tín dụng    │  │
│  │ Risk: [=====--] 58 │  │
│  │ 28,200,000 ₫       │  │
│  │ [Xem chi tiết →]   │  │
│  └────────────────────┘  │
│                          │
│  ┌────────────────────┐  │
│  │ 4. Trả thẳng       │  │
│  │ Risk: [======-] 71 │  │
│  │ 25,000,000 ₫       │  │
│  │ [Xem chi tiết →]   │  │
│  └────────────────────┘  │
│                          │
│ [Mô phỏng tác động]     │
│                          │
└──────────────────────────┘
```

**Interactions:**
- Option #1 (recommended) có viền highlight gradient + badge "Khuyến nghị"
- Mỗi card: animated entry (stagger), tap → mở detail
- Risk gauge là animated progress bar với color gradient
- "Mô phỏng tác động" → Navigate to Simulation page
- Swipe horizontally giữa các cards (carousel alternative)

### Page 4: Option Detail
**Layout:**
```
┌──────────────────────────┐
│ ← Chi tiết phương án      │
│                          │
│  Trả góp 6 tháng         │
│  ┌────────────────────┐  │
│  │   Risk Score: 32    │  │
│  │  [Large Gauge Ring] │  │
│  │   Rủi ro THẤP ✅    │  │
│  └────────────────────┘  │
│                          │
│  📊 So sánh chi tiết     │
│  ┌────────────────────┐  │
│  │ Tổng chi phí       │  │
│  │ 25,750,000 ₫       │  │
│  │────────────────────│  │
│  │ Thanh toán/tháng   │  │
│  │ 4,291,667 ₫        │  │
│  │────────────────────│  │
│  │ Lãi suất           │  │
│  │ 0.5%/tháng         │  │
│  │────────────────────│  │
│  │ Kỳ hạn             │  │
│  │ 6 tháng            │  │
│  └────────────────────┘  │
│                          │
│  📈 Tác động tài chính   │
│  ┌────────────────────┐  │
│  │ NCF:  5.2M → 4.3M  │  │
│  │ [=========|===]     │  │
│  │ DTI:  28% → 33%    │  │
│  │ [=======|===]       │  │
│  │ Save:  22% → 18%   │  │
│  │ [========|==]       │  │
│  └────────────────────┘  │
│                          │
│  🤖 Phân tích AI         │
│  ┌────────────────────┐  │
│  │ "Với thu nhập 18M   │  │
│  │ và chi phí cố định  │  │
│  │ 8.5M, trả góp 6    │  │
│  │ tháng là phương án  │  │
│  │ cân bằng tốt nhất. │  │
│  │ NCF giảm 17% nhưng │  │
│  │ vẫn dương, DTI tăng │  │
│  │ nhẹ nhưng dưới 35%.│  │
│  │ Bạn vẫn có thể duy │  │
│  │ trì mục tiêu tiết  │  │
│  │ kiệm mua xe."      │  │
│  └────────────────────┘  │
│                          │
│ [Home][Advisor][Health]  │
└──────────────────────────┘
```

### Page 5: Financial Health Dashboard
**Layout:**
```
┌──────────────────────────┐
│ Sức khỏe tài chính       │
│                          │
│  Overall: 72/100         │
│  [Large Animated Gauge]  │
│                          │
│  ┌────────────────────┐  │
│  │ 💵 Dòng tiền ròng  │  │
│  │ NCF = 5,200,000 ₫  │  │
│  │ [█████████░░] ✅    │  │
│  │ Thu nhập - Chi phí  │  │
│  │ - Tiết kiệm = NCF  │  │
│  └────────────────────┘  │
│                          │
│  ┌────────────────────┐  │
│  │ 📊 Tỷ lệ nợ/TN    │  │
│  │ DTI = 28%           │  │
│  │ [██████░░░░░] ✅    │  │
│  │ < 30% = An toàn    │  │
│  └────────────────────┘  │
│                          │
│  ┌────────────────────┐  │
│  │ 💰 Tỷ lệ tiết kiệm │  │
│  │ = 22%               │  │
│  │ [████████░░░] ✅    │  │
│  │ > 20% = Tốt        │  │
│  └────────────────────┘  │
│                          │
│  ┌────────────────────┐  │
│  │ 🛟 Quỹ khẩn cấp    │  │
│  │ EFR = 4.1 tháng    │  │
│  │ [██████░░░░░] ⚠️    │  │
│  │ Khuyến nghị: ≥ 6   │  │
│  └────────────────────┘  │
│                          │
│  🎯 Mục tiêu tài chính  │
│  ┌────────────────────┐  │
│  │ 🚗 Mua xe           │  │
│  │ 45% ████████░░░░   │  │
│  │ 90M / 200M         │  │
│  │────────────────────│  │
│  │ 🏠 Mua nhà          │  │
│  │ 12% ████░░░░░░░░   │  │
│  │ 120M / 1B          │  │
│  └────────────────────┘  │
│                          │
└──────────────────────────┘
```

### Page 6: Cash Flow Forecast
```
┌──────────────────────────┐
│ 📈 Dự báo dòng tiền      │
│                          │
│  ┌────────────────────┐  │
│  │ [LINE CHART]        │  │
│  │ Historical | Forecast│  │
│  │ (30 days)   (90 days)│  │
│  └────────────────────┘  │
│                          │
│  ┌──────┐ ┌──────┐      │
│  │30 ngày│ │90 ngày│      │
│  │+3.2M │ │+8.7M │      │
│  │  ↗️   │ │  ↗️   │      │
│  └──────┘ └──────┘      │
│                          │
│  Xu hướng: Ổn định ↗    │
│  "Dòng tiền dự kiến     │
│   tăng nhẹ trong 30     │
│   ngày tới"              │
│                          │
└──────────────────────────┘
```

### Page 7: Simulation (What-if)
```
┌──────────────────────────┐
│ 🔮 Mô phỏng tác động     │
│                          │
│  Nếu mua Laptop 25M     │
│  Phương án: Trả góp 6T  │
│                          │
│       TRƯỚC    SAU       │
│  NCF  5.2M  →  4.3M  ↘  │
│  DTI  28%   →  33%   ↗  │
│  Save 22%   →  18%   ↘  │
│  EFR  4.1   →  3.4   ↘  │
│  PGRS 0.72  →  0.65  ↘  │
│                          │
│  [Before/After Bar Chart]│
│                          │
│  ⚠️ Lưu ý:               │
│  EFR giảm dưới ngưỡng   │
│  an toàn (3.4 < 6 tháng)│
│                          │
│  💡 Gợi ý: Tăng kỳ hạn  │
│  lên 9 tháng để giảm    │
│  áp lực hàng tháng      │
│                          │
└──────────────────────────┘
```

---

## 2.4 Tech Stack (Frontend Rebuild)

| Technology | Purpose | Lý do |
|-----------|---------|-------|
| **React 18** | UI Framework | Giữ nguyên, đã quen |
| **TypeScript** | Type safety | Giữ nguyên |
| **Vite** | Build tool | Giữ nguyên |
| **Vanilla CSS** (CSS Modules) | Styling | Thay TailwindCSS → full control design system, animations premium |
| **Framer Motion** | Animations | Giữ nguyên, đã có |
| **Recharts** | Charts | Giữ nguyên |
| **React Router v6** | Navigation | **MỚI** — thay step-based navigation |
| **Zustand** | State | Giữ nguyên |
| **Inter** (Google Fonts) | Typography | Premium banking feel |

---

## 2.5 Backend Modifications

### Cần chỉnh sửa:

#### [MODIFY] `app/main.py`
- Thêm CORS cho frontend mới
- Đảm bảo demo profile seed phù hợp demo scenario

#### [MODIFY] `app/modules/advisory/service.py`
- Thêm field `recommendation_reason` vào response
- Ensure `explanation` field luôn có (cả khi Bedrock disabled)

#### [MODIFY] `app/modules/analysis/service.py`
- Thêm `overall_health_score` (0-100) — tổng hợp từ 6 chỉ số
- Thêm `status` cho mỗi metric (healthy/warning/critical)

#### [MODIFY] `app/modules/simulation/service.py`
- Thêm `suggestions` field — gợi ý cải thiện dựa trên kết quả simulation
- Thêm `alerts` khi metrics vượt ngưỡng

#### [MODIFY] `app/modules/advisory/scorer.py`
- Thêm document/comment giải thích trọng số scoring formula
- Reference Basel III / consumer credit risk literature

#### [NEW] `app/modules/analysis/schemas.py` — additions
- Thêm `OverallHealthResponse` schema với `overall_score`, per-metric `status`

### Không cần thay đổi:
- Forecasting module ✅
- Auth module ✅ (demo token)
- Goals module ✅
- Ingestion module ✅
- Core config ✅

---

## Verification Plan

### Automated Tests
```bash
# Backend
cd /Users/huypham/code/BNPL-Management
pytest -q

# Frontend (sau khi rebuild)
cd frontend
pnpm test
pnpm exec tsc --noEmit
```

### Manual Verification
1. Start backend: `uvicorn app.main:app --reload`
2. Start frontend: `cd frontend && pnpm dev`
3. Kiểm tra luồng demo đầy đủ:
   - Home Dashboard hiển thị metrics
   - Purchase input → Comparison results → Detail view
   - Financial Health page
   - Forecast chart
   - Simulation before/after
4. Kiểm tra responsive trong mobile viewport (375×812)
5. Kiểm tra animations smooth
6. Screenshot/Record video demo

### Demo Checklist
- [ ] Giao diện mobile-first chạy mượt
- [ ] Luồng demo scenario (mua laptop) hoạt động end-to-end
- [ ] AI explanation hiển thị đúng
- [ ] Charts render đẹp
- [ ] Animations smooth
- [ ] Color system nhất quán
- [ ] Không có lỗi console

---

## Execution Order

1. **Tạo Solution Summary document** → `solution_summary.md`
2. **Tạo Slide Deck content** → `slide_deck.md`
3. **Backend modifications** → thêm overall_health_score, suggestions, etc.
4. **Frontend rebuild** (ưu tiên theo thứ tự):
   - Design system (CSS variables, base components)
   - Mobile frame wrapper
   - Bottom navigation
   - Home Dashboard
   - Purchase Advisor input
   - Comparison Results
   - Option Detail
   - Financial Health page
   - Forecast page
   - Simulation page
5. **Testing & Polish**
6. **Record demo video**
