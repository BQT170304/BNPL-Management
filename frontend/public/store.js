/* ============================================================
   BNPL Assistant — backend-backed data layer (window.BNPL)
   Same surface the screens already use, but the compute calls
   now hit the real FastAPI backend via window.API (/api proxy).

   - Render-time reads (analyze/forecast/alerts/portfolio/feedback)
     return a cached value synchronously and fetch in the background,
     then trigger a re-render via __notify.
   - Handler calls (recommend/explain/copilot) are async (awaited).
   ============================================================ */
(function () {
  "use strict";
  const API = window.API;

  // ---------- formatters ----------
  const nf = new Intl.NumberFormat("vi-VN");
  const fmtVND = (n) => (n == null ? "—" : nf.format(Math.round(n)) + " ₫");
  const fmtNum = (n) => (n == null ? "—" : nf.format(Math.round(n)));
  const fmtPct = (n, d = 1) => (n == null ? "—" : Number(n).toFixed(d) + "%");
  const fmtMonth = (m) => m;
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const uid = (p) => p + Math.random().toString(36).slice(2, 8);
  const round1 = (n) => Math.round(n * 10) / 10;
  const round2 = (n) => Math.round(n * 100) / 100;

  // ---------- seed data (demo bootstrap; pushed to backend on load) ----------
  const CIFS = ["100", "200", "300"];
  const SEED = {
    "100": { cif: "100", income: 20000000, expense: 12000000, debt_payment: 4500000, subject: "Nguyễn Văn A" },
    "200": { cif: "200", income: 35000000, expense: 18000000, debt_payment: 6000000, subject: "Trần Thị B" },
    "300": { cif: "300", income: 14000000, expense: 9500000, debt_payment: 1800000, subject: "Lê Minh C" },
  };
  const OBLIGATION_SEEDS = {
    "100": [
      { source_key: "auto_tra_gop_dien_may", type: "BNPL", merchant: "Trả góp điện máy", category: "electronics",
        principal_amount: 9000000, monthly_payment: 1500000, due_day: 5, start_date: "2026-01-05", end_date: "2026-07-05",
        remaining_terms: 6, apr: 0.0, status: "ACTIVE", confidence: 0.42, evidence_count: 4, active_months: 6, total_paid: 6000000 },
      { source_key: "auto_the_tin_dung", type: "CREDIT_CARD", merchant: "Thẻ tín dụng VPB", category: "card",
        principal_amount: 18000000, monthly_payment: 2500000, due_day: 18, start_date: "2025-09-18", end_date: "2026-09-18",
        remaining_terms: 8, apr: 24.0, status: "ACTIVE", confidence: 0.88, evidence_count: 9, active_months: 9, total_paid: 22500000 },
    ],
    "200": [
      { source_key: "auto_vay_tieu_dung", type: "LOAN", merchant: "Vay tiêu dùng FE", category: "loan",
        principal_amount: 60000000, monthly_payment: 4000000, due_day: 10, start_date: "2025-06-10", end_date: "2026-12-10",
        remaining_terms: 7, apr: 18.0, status: "ACTIVE", confidence: 0.91, evidence_count: 12, active_months: 12, total_paid: 48000000 },
    ],
    "300": [
      { source_key: "auto_subscription", type: "SUBSCRIPTION", merchant: "Gói cước & streaming", category: "subscription",
        principal_amount: 0, monthly_payment: 600000, due_day: 1, start_date: "2025-01-01", end_date: "2026-12-01",
        remaining_terms: 7, apr: 0.0, status: "ACTIVE", confidence: 0.55, evidence_count: 3, active_months: 16, total_paid: 9600000 },
    ],
  };

  function defaultProfile() {
    return {
      id: "p1",
      income: { salary: 25000000, secondary: 0, avg_bonus_monthly: 1500000, passive: 0 },
      risk: "MEDIUM",
      emergency_fund: 30000000,
      expenses: [
        { category: "Thuê nhà", amount: 6000000, classification: "FIXED" },
        { category: "Ăn uống & sinh hoạt", amount: 4500000, classification: "SEMI_FIXED" },
        { category: "Đi lại", amount: 1500000, classification: "DISCRETIONARY" },
      ],
      debts: [
        { name: "Vay mua xe", monthly_payment: 2000000, balance: 20000000, apr: 12.0, months_remaining: 10, debt_type: "INSTALLMENT" },
        { name: "Thẻ tín dụng VPB", monthly_payment: 2500000, balance: 18000000, apr: 24.0, months_remaining: 8, debt_type: "REVOLVING" },
      ],
      assets: [
        { type: "CASH", value: 12000000, liquidity: "HIGH" },
        { type: "SAVINGS", value: 30000000, liquidity: "MEDIUM" },
      ],
      goals: [
        { id: "g1", name: "Mua nhà", target_amount: 300000000, deadline: "2030-01-01", priority: "HIGH", savings_allocated: 4000000 },
      ],
    };
  }

  function totals(p) {
    const income = (p.income.salary || 0) + (p.income.secondary || 0) + (p.income.avg_bonus_monthly || 0) + (p.income.passive || 0);
    const expense = p.expenses.reduce((s, e) => s + (+e.amount || 0), 0);
    const debt = p.debts.reduce((s, d) => s + (+d.monthly_payment || 0), 0);
    return { income, expense, debt };
  }
  function dtiBand(dti) {
    if (dti < 20) return "SAFE";
    if (dti < 35) return "ACCEPTABLE";
    if (dti < 40) return "WARNING";
    return "DANGER";
  }

  function OBLIGATION_FROM_SEED(seed, profileId) {
    return seed.map((s) => ({
      id: profileId + "_" + s.source_key, profile_id: profileId, type: s.type, merchant: s.merchant,
      category: s.category, principal_amount: s.principal_amount, monthly_payment: s.monthly_payment,
      due_day: s.due_day, start_date: s.start_date, end_date: s.end_date, remaining_terms: s.remaining_terms,
      apr: s.apr, status: s.status, confidence: s.confidence, verified: false, verified_by: null, verified_at: null,
    }));
  }
  function seedOutcomes() { return []; }

  // ---------- demo personas (real CIFs -> Prophet forecast) ----------
  const PERSONAS = {
    A: { key: "A", cif: "10000300", profileId: "persona_a", name: "Minh Anh",
         title: "Young Professional", blurb: "22–30 tuổi · mua sắm công nghệ · ít nghĩa vụ",
         risk: "MEDIUM", efMonths: 3,
         goals: [
           { id: "ga1", name: "Mua laptop mới", target_amount: 30000000, deadline: "2027-06-01", priority: "MEDIUM", savings_allocated: 3000000 },
           { id: "ga2", name: "Quỹ du lịch", target_amount: 20000000, deadline: "2027-01-01", priority: "LOW", savings_allocated: 1500000 },
         ] },
    B: { key: "B", cif: "10000317", profileId: "persona_b", name: "Quốc Hùng",
         title: "Nhiều nghĩa vụ", blurb: "28–40 tuổi · thẻ tín dụng + vay + BNPL + subscription",
         risk: "LOW", efMonths: 2,
         goals: [
           { id: "gb1", name: "Mua nhà", target_amount: 500000000, deadline: "2032-01-01", priority: "HIGH", savings_allocated: 8000000 },
         ] },
  };

  // ---------- sync cache + background fetch + notify ----------
  let _epoch = 0;
  let _notify = () => {};
  const _cache = new Map();
  const _inflight = new Set();

  function cachedRead(key, def, fetcher) {
    const k = _epoch + "|" + key;
    if (_cache.has(k)) return _cache.get(k);
    if (!_inflight.has(k)) {
      _inflight.add(k);
      Promise.resolve()
        .then(fetcher)
        .then((v) => { _cache.set(k, v); })
        .catch(() => { _cache.set(k, def); })
        .finally(() => { _inflight.delete(k); _notify(); });
    }
    return def;
  }

  const DEF_ANALYSIS = { ncf: 0, dti: 0, dti_band: "SAFE", saving_rate: 0, efr: 0, pgrs: 0, goals: [], flags: [] };
  const DEF_FORECAST = { profile_id: "", summary: { next_30_net: 0, next_90_net: 0, min_projected_balance: 0 }, months: [] };
  const DEF_PORTFOLIO = { total_customers: 0, evaluated_customers: 0, at_risk_count: 0, early_warned_count: 0, cross_sell_ready_count: 0, total_estimated_obligation: 0, estimated_npl_avoided: 0, assumed_default_reduction_rate: 0 };
  const DEF_FEEDBACK = { total_outcomes: 0, approval_outcome_rate: 0, late_rate: 0, false_approve_rate: 0, false_reject_rate: 0, counts: { PAID_ON_TIME: 0, LATE: 0, MISSED: 0, RESTRUCTURED: 0, DEFAULT: 0 } };

  // ---------- backend-backed reads (sync facade) ----------
  function analyze(p) { return cachedRead("analyze:" + p.id, DEF_ANALYSIS, () => API.analysis(p.id)); }
  function forecast(p, _obligations, months = 6) { return cachedRead("forecast:" + p.id + ":" + months, DEF_FORECAST, () => API.forecast(p.id, months)); }
  function alerts(p) { return cachedRead("alerts:" + p.id, { alerts: [] }, () => API.alerts(p.id, true)); }
  const DEF_DAILY = { profile_id: "", engine: "", history_days: 0, days: 0, starting_balance: 0, min_projected_balance: 0, points: [] };
  function dailyForecast(p, days = 90) { return cachedRead("daily:" + p.id + ":" + days, DEF_DAILY, () => API.dailyForecast(p.id, days)); }
  function portfolioSummary() { return cachedRead("portfolio", DEF_PORTFOLIO, () => API.portfolio()); }
  function feedbackMetrics() { return cachedRead("feedback", DEF_FEEDBACK, () => API.feedbackMetrics()); }

  // ---------- backend-backed handlers (async) ----------
  async function recommend(p, _obligations, input, createDecision, store) {
    const payload = {
      profile_id: p.id, item_name: input.item_name || "Khoản mua", amount: input.amount || 0,
      horizon_months: input.horizon_months || 6, apr: input.apr || 0, fee: input.fee || 0,
      late_fee: input.late_fee || 0, merchant_subsidy: input.merchant_subsidy || 0,
      record: !!createDecision,
    };
    if (input.tenor) payload.tenor = input.tenor;
    const rec = await API.recommend(payload);
    if (store && rec.decision_id) {
      store.decisions[rec.decision_id] = {
        decision_id: rec.decision_id, profile_id: p.id,
        input_snapshot: { profile_id: p.id, ...input }, recommendation: rec,
        model_version: "deterministic-v1", created_at: new Date().toISOString(), override: null, outcome: null,
      };
    }
    return rec;
  }

  async function explain(idOrDecision) {
    const id = typeof idOrDecision === "string" ? idOrDecision : (idOrDecision && idOrDecision.decision_id);
    return API.explain(id);
  }

  async function copilot(message, ctx) {
    const pid = ctx && ctx.profile ? ctx.profile.id : null;
    return API.copilot(message, pid);
  }

  // ---------- export ----------
  window.BNPL = {
    CIFS, SEED, OBLIGATION_SEEDS,
    fmtVND, fmtNum, fmtPct, fmtMonth, uid, clamp, round1, round2,
    defaultProfile, totals, dtiBand, OBLIGATION_FROM_SEED, seedOutcomes, PERSONAS,
    analyze, alerts, forecast, dailyForecast, recommend, explain, copilot,
    portfolioSummary, feedbackMetrics,
    __setNotify: (fn) => { _notify = fn; },
    __invalidate: () => { _epoch++; _cache.clear(); _notify(); },
  };
})();
