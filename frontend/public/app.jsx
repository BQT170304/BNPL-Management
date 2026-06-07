/* ============================================================
   BNPL Assistant — App shell, routing, state, tweaks
   ============================================================ */
const AB = window.BNPL;
const API = window.API;
const { useState, useEffect, useRef } = React;

// strip UI-only fields -> ObligationIn for the backend
function toObligationIn(o) {
  return {
    id: o.id, type: o.type, merchant: o.merchant, category: o.category || "debt",
    principal_amount: o.principal_amount || 0, monthly_payment: o.monthly_payment || 0,
    due_day: o.due_day || 1, start_date: o.start_date || new Date().toISOString().slice(0, 10),
    end_date: o.end_date || null, remaining_terms: o.remaining_terms ?? null,
    apr: o.apr || 0, status: o.status || "ACTIVE", confidence: o.confidence ?? 1.0,
  };
}

const NAV = {
  user: [
    { key: "consent", label: "Cấp quyền CIF", icon: "key", comp: "ConsentScreen", n: 1 },
    { key: "profile", label: "Hồ sơ tài chính", icon: "user", comp: "ProfileScreen", n: 2 },
    { key: "health", label: "Sức khỏe", icon: "heart", comp: "HealthScreen", n: 3 },
    { key: "obligations", label: "Nghĩa vụ", icon: "list", comp: "ObligationsScreen", n: 4 },
    { key: "forecast", label: "Dự báo dòng tiền", icon: "chart", comp: "ForecastScreen", n: 5 },
    { key: "planning", label: "Mô phỏng & Khuyến nghị", icon: "cart", comp: "PlanningScreen", n: 6 },
    { key: "copilot", label: "Copilot", icon: "chat", comp: "CopilotScreen", n: 7 },
  ],
  rm: [
    { key: "consentAudit", label: "Cấp quyền & Audit", icon: "key", comp: "ConsentAuditScreen", n: 8 },
    { key: "review", label: "RM Review", icon: "gavel", comp: "RMReviewScreen", n: 9 },
    { key: "verify", label: "Xác minh nghĩa vụ", icon: "check", comp: "VerifyScreen", n: 10 },
    { key: "feedback", label: "Feedback & Outcomes", icon: "feedback", comp: "FeedbackScreen", n: 11 },
    { key: "portfolio", label: "Portfolio", icon: "grid", comp: "PortfolioScreen", n: 12 },
  ],
};
const ALL = [...NAV.user, ...NAV.rm];

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "accentHue": 60,
  "glassAlpha": 0.055,
  "glassBlur": 22,
  "radius": 18,
  "density": "regular",
  "animatedBg": true
}/*EDITMODE-END*/;

const HUES = [
  { h: 60, name: "Cam" }, { h: 295, name: "Tím" }, { h: 255, name: "Lam" }, { h: 195, name: "Lục lam" }, { h: 338, name: "Hồng" }, { h: 150, name: "Lục" },
];

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [toastNode, toast] = useToast();
  const storeRef = useRef({ decisions: {} });
  const [, tick] = useState(0);
  const rerender = () => tick(x => x + 1);

  // ---- initial seeded state (alive demo) ----
  const [role, setRole] = useState("user");
  const [screen, setScreen] = useState("health");
  const [currentCif, setCurrentCif] = useState("100");
  const [consents, setConsents] = useState(() => [{
    consent_id: AB.uid("cons_"), cif: "100", scopes: ["CIF_SUMMARY", "CIF_TRANSACTIONS"], status: "GRANTED",
    granted_by: "user-self", subject: AB.SEED["100"].subject, granted_at: new Date().toISOString(), expires_at: null, revoked_at: null,
  }]);
  const [profile, setProfile] = useState(() => AB.defaultProfile());
  const [obligations, setObligations] = useState(() => AB.OBLIGATION_FROM_SEED(AB.OBLIGATION_SEEDS["100"], "p1"));
  const [decisionIds, setDecisionIds] = useState([]);
  const [activeDecision, setActiveDecision] = useState(null);
  const [outcomePrompt, setOutcomePrompt] = useState(null);
  const [outcomes, setOutcomes] = useState(() => AB.seedOutcomes());
  const [copilotMsgs, setCopilotMsgs] = useState([]);

  // ---- apply tweaks to :root ----
  useEffect(() => {
    const r = document.documentElement.style;
    r.setProperty("--accent-h", t.accentHue);
    r.setProperty("--glass-a", t.glassAlpha);
    r.setProperty("--glass-blur", t.glassBlur + "px");
    r.setProperty("--radius", t.radius + "px");
    r.setProperty("--pad", t.density === "compact" ? 0.78 : t.density === "comfy" ? 1.18 : 1);
  }, [t]);

  // ---- wire BNPL re-render notifications ----
  useEffect(() => { AB.__setNotify(rerender); }, []);

  // ---- bootstrap demo data into the real backend (once) ----
  const booted = useRef(false);
  useEffect(() => {
    if (booted.current) return;
    booted.current = true;
    (async () => {
      try {
        await API.grantConsent({ cif: "100", scopes: ["CIF_SUMMARY", "CIF_TRANSACTIONS"],
          granted_by: "user-self", subject: AB.SEED["100"].subject, ttl_days: 90 });
        await API.createProfile(AB.defaultProfile());
        const seeded = AB.OBLIGATION_FROM_SEED(AB.OBLIGATION_SEEDS["100"], "p1");
        for (const o of seeded) { try { await API.createObligation("p1", toObligationIn(o)); } catch (_) {} }
        AB.__invalidate();
        toast("Đã kết nối backend (dữ liệu demo đã nạp)");
      } catch (e) {
        toast("Không kết nối được backend: " + e.message, "danger");
      }
    })();
  }, []);

  const state = { role, screen, currentCif, consents, profile, obligations, decisionIds, activeDecision, outcomePrompt, outcomes, copilotMsgs, store: storeRef.current };

  const refresh = () => AB.__invalidate();

  const actions = {
    toast,
    go: (sc, r) => { if (r) setRole(r); setScreen(sc); },
    setCif: setCurrentCif,
    grantConsent: async (payload) => {
      try {
        await API.grantConsent({ cif: payload.cif, scopes: payload.scopes,
          granted_by: payload.granted_by, subject: payload.subject, ttl_days: payload.ttl_days || null });
      } catch (e) { toast("Cấp quyền lỗi: " + e.message, "danger"); return; }
      setConsents(prev => {
        const filtered = prev.filter(c => !(c.cif === payload.cif && c.status === "GRANTED"));
        return [...filtered, { consent_id: AB.uid("cons_"), status: "GRANTED", granted_at: new Date().toISOString(),
          expires_at: payload.ttl_days ? new Date(Date.now() + payload.ttl_days * 864e5).toISOString() : null, revoked_at: null, ...payload }];
      });
      refresh(); toast(`Đã cấp quyền cho CIF ${payload.cif}`);
    },
    revokeConsent: async (id) => {
      const c = consents.find(x => x.consent_id === id);
      if (c && c.consent_id && c.consent_id.startsWith("cons_") && c.__backend_id) {
        try { await API.revokeConsent(c.__backend_id); } catch (e) { toast(e.message, "danger"); }
      }
      setConsents(prev => prev.map(x => x.consent_id === id ? { ...x, status: "REVOKED", revoked_at: new Date().toISOString() } : x));
      toast("Đã thu hồi consent", "danger");
    },
    saveProfile: async (p) => {
      try { await API.createProfile(p); } catch (e) { toast("Lưu hồ sơ lỗi: " + e.message, "danger"); return; }
      setProfile(structuredClone(p)); refresh(); toast(`Đã lưu hồ sơ ${p.id}`);
    },
    seedObligations: async () => {
      const consent = consents.find(c => c.cif === currentCif && c.status === "GRANTED" && c.scopes.includes("CIF_TRANSACTIONS"));
      if (!consent) { toast("Cần consent CIF_TRANSACTIONS", "danger"); return; }
      const pid = profile ? profile.id : "p1";
      const seeded = AB.OBLIGATION_FROM_SEED(AB.OBLIGATION_SEEDS[currentCif] || [], pid);
      try { for (const o of seeded) await API.createObligation(pid, toObligationIn(o)); }
      catch (e) { toast("Seed lỗi: " + e.message, "danger"); }
      setObligations(prev => { const keys = new Set(prev.map(o => o.id)); return [...prev, ...seeded.filter(o => !keys.has(o.id))]; });
      refresh(); toast(`Đã seed ${seeded.length} nghĩa vụ từ CIF ${currentCif}`);
    },
    addObligation: async (draft) => {
      const pid = profile ? profile.id : "p1";
      const o = { id: pid + "_man_" + AB.uid(""), profile_id: pid, ...draft,
        start_date: new Date().toISOString().slice(0, 10), end_date: null, confidence: 1.0, verified: false, verified_by: null, verified_at: null };
      try { await API.createObligation(pid, toObligationIn(o)); } catch (e) { toast("Thêm nghĩa vụ lỗi: " + e.message, "danger"); return; }
      setObligations(prev => [...prev, o]); refresh(); toast("Đã thêm nghĩa vụ");
    },
    deleteObligation: async (id) => {
      const pid = profile ? profile.id : "p1";
      try { await API.deleteObligation(pid, id); } catch (e) { toast("Xoá lỗi: " + e.message, "danger"); }
      setObligations(prev => prev.filter(o => o.id !== id)); refresh(); toast("Đã xoá nghĩa vụ", "danger");
    },
    verifyObligation: async (id, by) => {
      try { await API.verifyObligation(id, by); } catch (e) { toast("Xác minh lỗi: " + e.message, "danger"); return; }
      setObligations(prev => prev.map(o => o.id === id ? { ...o, verified: true, verified_by: by, verified_at: new Date().toISOString(), confidence: 1.0 } : o));
      refresh(); toast(`Đã xác minh bởi ${by}`);
    },
    registerDecision: (id) => setDecisionIds(prev => prev.includes(id) ? prev : [...prev, id]),
    openDecision: (id) => { setActiveDecision(id); setRole("rm"); setScreen("review"); },
    overrideDecision: async (id, payload) => {
      try { await API.override(id, { actor: payload.actor, action: payload.action, reason: payload.reason, scenario_id: payload.scenario_id || null }); }
      catch (e) { toast("Override lỗi: " + e.message, "danger"); return; }
      const dec = storeRef.current.decisions[id];
      if (dec) dec.override = { decision_id: id, created_at: new Date().toISOString(), ...payload };
      rerender(); toast(`Đã ${payload.action} quyết định`);
    },
    recordOutcomePrompt: (id) => setOutcomePrompt(id),
    recordOutcome: async ({ decision_id, outcome, recorded_by, note }) => {
      try { await API.recordOutcome(decision_id, { outcome, recorded_by, note: note || null }); }
      catch (e) { toast("Ghi outcome lỗi: " + e.message, "danger"); return; }
      const dec = storeRef.current.decisions[decision_id];
      setOutcomes(prev => [...prev, { id: AB.uid("out_"), decision_id, profile_id: "p1", outcome, recorded_by,
        recorded_at: new Date().toISOString(), note, item_name: dec ? dec.recommendation.item_name : decision_id }]);
      refresh(); toast("Đã ghi nhận outcome: " + outcome);
    },
    loadPersona: async (key) => {
      const per = AB.PERSONAS[key];
      if (!per) return;
      try {
        await API.grantConsent({ cif: per.cif, scopes: ["CIF_SUMMARY", "CIF_TRANSACTIONS"],
          granted_by: "demo", subject: per.name, ttl_days: 90 });
        let seed;
        try { seed = await API.cifSeed(per.cif, "average"); }
        catch (e) { seed = { income: 25000000, expense: 12000000, debt_payment: 3000000 }; }
        const ef = Math.round(seed.expense * per.efMonths);
        const profile = {
          id: per.profileId, income: { salary: seed.income, secondary: 0, avg_bonus_monthly: 0, passive: 0 },
          risk: per.risk, emergency_fund: ef,
          expenses: [{ category: "Chi tiêu hàng tháng", amount: seed.expense, classification: "SEMI_FIXED" }],
          debts: [],
          assets: [{ type: "CASH", value: seed.income, liquidity: "HIGH" }, { type: "SAVINGS", value: ef, liquidity: "MEDIUM" }],
          goals: per.goals,
        };
        await API.createProfile(profile);
        try { await API.seedFromCif(per.profileId, per.cif); } catch (e) {}
        let obs = [];
        try { const r = await API.listObligations(per.profileId); obs = r.obligations || []; } catch (e) {}
        setConsents([{ consent_id: AB.uid("cons_"), cif: per.cif, scopes: ["CIF_SUMMARY", "CIF_TRANSACTIONS"],
          status: "GRANTED", granted_by: "demo", subject: per.name, granted_at: new Date().toISOString(), expires_at: null, revoked_at: null }]);
        setCurrentCif(per.cif); setProfile(profile); setObligations(obs);
        AB.__invalidate(); setRole("user"); setScreen("health");
        toast(`Đã nạp Persona ${key} · CIF ${per.cif} · ${obs.length} nghĩa vụ (Prophet)`);
      } catch (e) { toast("Nạp persona lỗi: " + e.message, "danger"); }
    },
    sendCopilot: async (text) => {
      setCopilotMsgs(prev => [...prev, { role: "user", text }]);
      let res;
      try { res = await AB.copilot(text, { profile, obligations }); }
      catch (e) { setCopilotMsgs(prev => [...prev, { role: "bot", text: "Lỗi: " + e.message }]); return; }
      if (res.decision_id) {
        setDecisionIds(prev => prev.includes(res.decision_id) ? prev : [...prev, res.decision_id]);
        try {
          const d = await API.getDecision(res.decision_id);
          storeRef.current.decisions[res.decision_id] = { decision_id: res.decision_id, profile_id: d.profile_id,
            input_snapshot: d.input_snapshot, recommendation: d.recommendation, model_version: d.model_version,
            created_at: d.created_at, override: d.override, outcome: null };
        } catch (_) {}
      }
      setCopilotMsgs(prev => [...prev, { role: "bot", text: res.reply, meta: res }]);
    },
  };
  const ctx = { state, actions };

  const nav = NAV[role];
  const active = ALL.find(s => s.key === screen) || nav[0];
  const Comp = window[active.comp];
  const subjectName = AB.SEED[currentCif] ? AB.SEED[currentCif].subject : "";

  return (
    <>
      <div className={"aurora " + (t.animatedBg ? "" : "static")}><div className="grid" /></div>
      <div style={{ position: "relative", zIndex: 1, display: "grid", gridTemplateColumns: "264px 1fr", height: "100vh" }}>
        {/* SIDEBAR */}
        <aside className="glass" style={{ margin: 14, marginRight: 0, borderRadius: "var(--radius-lg)", display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div style={{ padding: "20px 20px 16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 11 }}>
              <div style={{ width: 38, height: 38, borderRadius: 12, background: "linear-gradient(150deg, var(--accent), var(--accent-strong))", display: "grid", placeItems: "center", boxShadow: "0 8px 22px -8px var(--accent-glow)", color: "#0a0712" }}><Icon name="bolt" size={20} /></div>
              <div>
                <div style={{ fontWeight: 700, letterSpacing: "-0.02em", fontSize: 15 }}>BNPL Assistant</div>
                <div style={{ fontSize: 11, color: "var(--ink-3)" }}>Mua trả góp thông minh</div>
              </div>
            </div>
          </div>

          {/* role switch */}
          <div style={{ padding: "0 16px 14px" }}>
            <div className="seg" style={{ width: "100%", display: "grid", gridTemplateColumns: "1fr 1fr" }}>
              <button className={role === "user" ? "on" : ""} onClick={() => { setRole("user"); setScreen("health"); }}>End-user</button>
              <button className={role === "rm" ? "on" : ""} onClick={() => { setRole("rm"); setScreen("review"); }}>RM / Operator</button>
            </div>
          </div>

          {/* demo persona picker (real CIF -> Prophet) */}
          <div style={{ padding: "0 16px 14px" }}>
            <div className="eyebrow" style={{ padding: "2px 2px 7px" }}>Demo persona · CIF thật · Prophet</div>
            <div style={{ display: "grid", gap: 7 }}>
              {["A", "B"].map((k) => {
                const per = AB.PERSONAS[k];
                const on = currentCif === per.cif;
                return (
                  <button key={k} className="glass-flat" onClick={() => actions.loadPersona(k)}
                    style={{ textAlign: "left", padding: "9px 11px", borderRadius: 11, cursor: "pointer",
                      border: on ? "1px solid var(--accent)" : "1px solid var(--glass-line)", background: on ? "var(--accent-soft)" : undefined }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
                      <span style={{ width: 18, height: 18, borderRadius: 6, background: "var(--accent-soft)", color: "var(--accent)", display: "grid", placeItems: "center", fontSize: 11, fontWeight: 700 }}>{k}</span>
                      <span style={{ fontSize: 12.5, fontWeight: 600 }}>{per.title}</span>
                    </div>
                    <div style={{ fontSize: 10.5, color: "var(--ink-3)", marginTop: 4, lineHeight: 1.35 }}>{per.blurb}</div>
                  </button>
                );
              })}
            </div>
          </div>

          <nav style={{ flex: 1, overflowY: "auto", padding: "4px 12px 12px", display: "grid", gap: 3, alignContent: "start" }}>
            <div className="eyebrow" style={{ padding: "8px 10px 4px" }}>{role === "user" ? "Hành trình khách hàng" : "Vận hành ngân hàng"}</div>
            {nav.map(s => {
              const on = s.key === screen;
              return (
                <button key={s.key} className="nav-item" onClick={() => setScreen(s.key)}
                  style={{ display: "flex", alignItems: "center", gap: 11, padding: "10px 11px", borderRadius: 11, border: "none", cursor: "pointer", textAlign: "left", width: "100%",
                    background: on ? "var(--accent-soft)" : "transparent", color: on ? "var(--ink)" : "var(--ink-2)",
                    fontSize: 13.5, fontWeight: on ? 600 : 500, transition: "background .15s, color .15s", position: "relative" }}
                  onMouseEnter={e => { if (!on) e.currentTarget.style.background = "rgba(255,255,255,0.04)"; }}
                  onMouseLeave={e => { if (!on) e.currentTarget.style.background = "transparent"; }}>
                  {on && <span style={{ position: "absolute", left: -12, top: "50%", transform: "translateY(-50%)", width: 3, height: 20, borderRadius: 3, background: "var(--accent)" }} />}
                  <span style={{ color: on ? "var(--accent)" : "var(--ink-3)", display: "grid", placeItems: "center", width: 22 }}><Icon name={s.icon} size={17} /></span>
                  <span style={{ flex: 1 }}>{s.label}</span>
                  <span className="num" style={{ fontSize: 10.5, color: "var(--ink-4)", fontWeight: 600 }}>{String(s.n).padStart(2, "0")}</span>
                </button>
              );
            })}
          </nav>

          <div style={{ padding: 14, borderTop: "1px solid var(--glass-line)", display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 32, height: 32, borderRadius: 10, background: "rgba(255,255,255,0.06)", display: "grid", placeItems: "center", color: "var(--ink-2)" }}><Icon name="user" size={16} /></div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 12.5, fontWeight: 600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{role === "user" ? subjectName : "RM Alice"}</div>
              <div className="mono" style={{ fontSize: 10.5, color: "var(--ink-3)" }}>{role === "user" ? `CIF ${currentCif} · p1` : "operator"}</div>
            </div>
          </div>
        </aside>

        {/* MAIN */}
        <main style={{ overflowY: "auto", height: "100vh" }}>
          <div style={{ maxWidth: 1140, margin: "0 auto", padding: "30px 34px 60px", minHeight: "100%" }} key={screen}>
            {Comp ? <Comp ctx={ctx} /> : <div>—</div>}
          </div>
        </main>
      </div>

      {toastNode}

      <TweaksPanel>
        <TweakSection label="Màu nhấn" />
        <div style={{ display: "flex", gap: 9, padding: "2px 2px 6px" }}>
          {HUES.map(h => (
            <button key={h.h} title={h.name} onClick={() => setTweak("accentHue", h.h)}
              style={{ width: 30, height: 30, borderRadius: "50%", cursor: "pointer", flex: "none",
                background: `oklch(0.70 0.17 ${h.h})`, border: t.accentHue === h.h ? "2.5px solid #fff" : "2.5px solid transparent",
                boxShadow: t.accentHue === h.h ? `0 0 0 2px oklch(0.70 0.17 ${h.h})` : "none", transition: "all .15s" }} />
          ))}
        </div>
        <TweakSection label="Lớp kính" />
        <TweakSlider label="Độ blur" value={t.glassBlur} min={4} max={36} step={1} unit="px" onChange={v => setTweak("glassBlur", v)} />
        <TweakSlider label="Độ trong" value={t.glassAlpha} min={0.02} max={0.13} step={0.005} onChange={v => setTweak("glassAlpha", v)} />
        <TweakSlider label="Bo góc" value={t.radius} min={6} max={28} step={1} unit="px" onChange={v => setTweak("radius", v)} />
        <TweakSection label="Bố cục" />
        <TweakRadio label="Mật độ" value={t.density} options={["compact", "regular", "comfy"]} onChange={v => setTweak("density", v)} />
        <TweakToggle label="Nền động (aurora)" value={t.animatedBg} onChange={v => setTweak("animatedBg", v)} />
      </TweaksPanel>
    </>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
