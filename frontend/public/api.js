/* ============================================================
   BNPL Assistant — real backend client (window.API)
   All calls go through the Vite proxy at /api (-> FastAPI).
   ============================================================ */
(function () {
  "use strict";
  const BASE = "/api";

  async function req(path, init) {
    let res;
    try {
      res = await fetch(BASE + path, {
        ...init,
        headers: { "Content-Type": "application/json", ...((init && init.headers) || {}) },
      });
    } catch (e) {
      throw new Error("Không kết nối được máy chủ");
    }
    const text = await res.text();
    const data = text ? JSON.parse(text) : null;
    if (!res.ok) {
      const detail = data && data.detail ? data.detail : "Lỗi máy chủ (" + res.status + ")";
      const err = new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
      err.status = res.status;
      err.body = data;
      throw err;
    }
    return data;
  }
  const get = (p) => req(p, { method: "GET" });
  const post = (p, body) => req(p, { method: "POST", body: body == null ? undefined : JSON.stringify(body) });
  const del = (p) => req(p, { method: "DELETE" });

  window.API = {
    // consent
    grantConsent: (b) => post("/consents", b),
    getConsent: (id) => get("/consents/" + id),
    revokeConsent: (id) => post("/consents/" + id + "/revoke"),
    listCifConsents: (cif) => get("/cifs/" + cif + "/consents"),
    profileCifs: (pid) => get("/profiles/" + pid + "/cifs"),
    // ingestion
    listCifs: () => get("/ingestion/cifs"),
    cifSeed: (cif, strategy = "latest") => get("/ingestion/cif/" + cif + "/seed?strategy=" + strategy),
    obligationSeeds: (cif) => get("/ingestion/cif/" + cif + "/obligation-seeds"),
    seedFromCif: (pid, cif) => post("/profiles/" + pid + "/obligations/from-cif/" + cif),
    // profiles
    createProfile: (p) => post("/profiles", p),
    analysis: (pid) => get("/profiles/" + pid + "/analysis"),
    alerts: (pid, includeForecast = true) =>
      get("/profiles/" + pid + "/alerts" + (includeForecast ? "?include_forecast=true" : "")),
    forecast: (pid, months = 6) => get("/profiles/" + pid + "/forecast?months=" + months),
    dailyForecast: (pid, days = 90) => get("/profiles/" + pid + "/forecast/daily?days=" + days),
    // obligations
    listObligations: (pid) => get("/profiles/" + pid + "/obligations"),
    createObligation: (pid, o) => post("/profiles/" + pid + "/obligations", o),
    deleteObligation: (pid, oid) => del("/profiles/" + pid + "/obligations/" + oid),
    verifyObligation: (oid, verifiedBy) => post("/obligations/" + oid + "/verify", { verified_by: verifiedBy }),
    // planning
    recommend: (input) => post("/planning/recommend", input),
    simulate: (input) => post("/planning/simulate", input),
    // decisions
    getDecision: (id) => get("/decisions/" + id),
    explain: (id) => post("/decisions/" + id + "/explain"),
    override: (id, b) => post("/decisions/" + id + "/override", b),
    recordOutcome: (id, b) => post("/decisions/" + id + "/outcomes", b),
    // feedback / portfolio
    feedbackMetrics: () => get("/feedback/metrics"),
    feedbackDataset: () => get("/feedback/dataset"),
    feedbackOutcomes: () => get("/feedback/outcomes"),
    portfolio: () => get("/portfolio/summary"),
    // copilot
    copilot: (message, profile_id, decision_id) => post("/copilot/chat", { message, profile_id, decision_id }),
    // health
    health: () => get("/health"),
  };
})();
