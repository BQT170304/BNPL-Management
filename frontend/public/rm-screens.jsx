/* ============================================================
   BNPL Assistant — RM / Operator screens (8–12)
   ============================================================ */
const RB = window.BNPL;
const { useState, useEffect } = React;

/* ============ 8. CONSENT AUDIT ============ */
function ConsentAuditScreen({ ctx }) {
  const { state, actions } = ctx;
  const [cif, setCif] = useState("100");
  const [scopes, setScopes] = useState(["CIF_SUMMARY", "CIF_TRANSACTIONS"]);
  const [actor, setActor] = useState("rm_alice");
  const [subject, setSubject] = useState("");
  const list = state.consents.filter(c => c.cif === cif);
  const toggle = (s) => setScopes(p => p.includes(s) ? p.filter(x => x !== s) : [...p, s]);

  return (
    <div className="stagger" style={{ display: "grid", gap: 20 }}>
      <SectionHead eyebrow="RM · Flow C" title="Cấp quyền & Audit consent"
        sub="RM cấp/thu hồi quyền truy cập CIF thay khách và xem ai đã cấp quyền nào (audit theo CIF)." />
      <div style={{ display: "grid", gridTemplateColumns: "360px 1fr", gap: 20, alignItems: "start" }}>
        <Card style={{ display: "grid", gap: 16 }}>
          <div className="h-title">Cấp quyền mới</div>
          <Field label="CIF"><Select value={cif} onChange={setCif} options={RB.CIFS.map(c => ({ value: c, label: `CIF ${c} · ${RB.SEED[c].subject}` }))} /></Field>
          <Field label="Cấp bởi (RM)"><TextInput value={actor} onChange={setActor} /></Field>
          <Field label="Chủ thể (subject)"><TextInput value={subject} onChange={setSubject} placeholder={RB.SEED[cif].subject} /></Field>
          <Field label="Scopes">
            <div style={{ display: "grid", gap: 8, marginTop: 2 }}>
              <Checkbox checked={scopes.includes("CIF_SUMMARY")} onChange={() => toggle("CIF_SUMMARY")}>CIF_SUMMARY</Checkbox>
              <Checkbox checked={scopes.includes("CIF_TRANSACTIONS")} onChange={() => toggle("CIF_TRANSACTIONS")}>CIF_TRANSACTIONS</Checkbox>
            </div>
          </Field>
          <Btn variant="primary" icon="key" disabled={!scopes.length}
            onClick={() => actions.grantConsent({ cif, scopes, granted_by: actor, subject: subject || RB.SEED[cif].subject, ttl_days: 90 })}>Cấp quyền</Btn>
        </Card>

        <Card pad={false} style={{ overflow: "hidden" }}>
          <div style={{ padding: "16px 20px" }} className="h-title">Lịch sử consent · CIF {cif}</div>
          {list.length ? (
            <table className="tbl">
              <thead><tr><th>Consent ID</th><th>Scopes</th><th>Cấp bởi</th><th>Trạng thái</th><th></th></tr></thead>
              <tbody>
                {list.map(c => (
                  <tr key={c.consent_id} className="row-hover">
                    <td className="mono" style={{ fontSize: 11.5 }}>{c.consent_id}</td>
                    <td><div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>{c.scopes.map(s => <span key={s} className="chip mono" style={{ fontSize: 10 }}>{s.replace("CIF_", "")}</span>)}</div></td>
                    <td style={{ fontSize: 12.5 }}>{c.granted_by}</td>
                    <td><StatusBadge value={c.status} /></td>
                    <td className="right">{c.status === "GRANTED" && <Btn size="sm" variant="danger" onClick={() => actions.revokeConsent(c.consent_id)}>Thu hồi</Btn>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <Empty icon="key" title="Chưa có consent" sub={`CIF ${cif} chưa được cấp quyền lần nào.`} />}
        </Card>
      </div>
    </div>
  );
}

/* ============ 9. RM REVIEW ============ */
function RMReviewScreen({ ctx }) {
  const { state, actions } = ctx;
  const ids = state.decisionIds;
  const [sel, setSel] = useState(state.activeDecision || ids[ids.length - 1] || null);
  const [action, setAction] = useState("APPROVE");
  const [reason, setReason] = useState("");
  useEffect(() => { if (state.activeDecision) setSel(state.activeDecision); }, [state.activeDecision]);

  if (!ids.length) return <Card><Empty icon="gavel" title="Chưa có quyết định" sub="Hãy chạy Mô phỏng & Khuyến nghị (có lưu) ở vai End-user để tạo quyết định cho RM review."
    action={<Btn variant="primary" onClick={() => actions.go("planning", "user")}>Tới màn Mô phỏng</Btn>} /></Card>;

  const dec = state.store.decisions[sel] || state.store.decisions[ids[ids.length - 1]];
  const rec = dec.recommendation;
  const best = rec.scenarios.find(s => s.scenario.scenario_id === rec.best_scenario_id);

  const submit = () => {
    if (!reason.trim()) { actions.toast("Lý do override là bắt buộc", "danger"); return; }
    actions.overrideDecision(dec.decision_id, { actor: "rm_alice", action, reason: reason.trim(), scenario_id: null });
    setReason("");
  };

  return (
    <div className="stagger" style={{ display: "grid", gap: 20 }}>
      <SectionHead eyebrow="RM · Flow C" title="RM Review — quyết định"
        sub="Đối chiếu quyết định của máy với phán quyết của người. Mọi override yêu cầu lý do (non-empty)."
        right={<Select value={sel} onChange={setSel} options={ids.map(id => ({ value: id, label: id }))} />} />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, alignItems: "start" }}>
        <Card style={{ display: "grid", gap: 14 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <Badge tone="info" dot>Quyết định của máy</Badge>
            <span className="mono" style={{ fontSize: 11, color: "var(--ink-3)" }}>{dec.model_version}</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <ScoreRing score={best.score} />
            <div>
              <div className="h-title">{best.scenario.label}</div>
              <div style={{ fontSize: 12.5, color: "var(--ink-2)", marginTop: 4 }}>{rec.item_name} · {RB.fmtVND(rec.amount)}</div>
            </div>
          </div>
          <div style={{ fontSize: 13, color: "var(--ink-2)", lineHeight: 1.5 }}>{rec.summary}</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <div className="glass-flat" style={{ padding: 11 }}><div className="eyebrow">Trả/tháng</div><div className="num" style={{ fontWeight: 700, marginTop: 3 }}>{RB.fmtVND(best.scenario.monthly_payment)}</div></div>
            <div className="glass-flat" style={{ padding: 11 }}><div className="eyebrow">DTI sau</div><div className="num" style={{ fontWeight: 700, marginTop: 3 }}>{best.scenario.metrics.max_dti}%</div></div>
          </div>
          {rec.advisories.length > 0 && <div style={{ display: "flex", gap: 5, flexWrap: "wrap" }}>{rec.advisories.map(a => <Badge key={a} tone="warn">{a}</Badge>)}</div>}
          <Btn size="sm" icon="info" onClick={async () => { try { const ex = await RB.explain(dec.decision_id); actions.toast(ex.key_reasons[0]); } catch (e) { actions.toast(e.message, "danger"); } }}>Xem giải thích</Btn>
        </Card>

        <Card style={{ display: "grid", gap: 14 }}>
          <Badge tone={dec.override ? "accent" : "muted"} dot>Phán quyết của người (RM)</Badge>
          {dec.override ? (
            <div className="glass-flat" style={{ padding: 16, display: "grid", gap: 10, borderLeft: `2.5px solid ${dec.override.action === "REJECT" ? "var(--danger)" : dec.override.action === "APPROVE" ? "var(--safe)" : "var(--warn)"}` }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}><StatusBadge value={dec.override.action} /><span style={{ fontSize: 13, fontWeight: 600 }}>bởi {dec.override.actor}</span></div>
              <div style={{ fontSize: 13, color: "var(--ink-2)" }}>"{dec.override.reason}"</div>
              <div className="mono" style={{ fontSize: 11, color: "var(--ink-3)" }}>{new Date(dec.override.created_at).toLocaleString("vi-VN")}</div>
            </div>
          ) : (
            <>
              <Field label="Hành động"><Segmented value={action} onChange={setAction} options={["APPROVE", "REJECT", "OVERRIDE"]} /></Field>
              <Field label="Lý do (bắt buộc)"><textarea className="input" rows={4} value={reason} onChange={(e) => setReason(e.target.value)} placeholder="VD: Khách sắp thay đổi thu nhập, cần thận trọng…" /></Field>
              <Btn variant="primary" icon="gavel" disabled={!reason.trim()} onClick={submit}>Ghi nhận phán quyết</Btn>
              <div style={{ fontSize: 11.5, color: "var(--ink-3)" }}>Thiếu lý do → backend trả 422. Nút bị khoá tới khi nhập lý do.</div>
            </>
          )}
          {dec.override && <Btn variant="ghost" size="sm" onClick={() => { actions.recordOutcomePrompt(dec.decision_id); actions.go("feedback"); }}>Ghi nhận kết quả thực tế →</Btn>}
        </Card>
      </div>
    </div>
  );
}

/* ============ 10. VERIFY OBLIGATIONS ============ */
function VerifyScreen({ ctx }) {
  const { state, actions } = ctx;
  const need = state.obligations.filter(o => o.confidence < 0.7 && !o.verified);
  const done = state.obligations.filter(o => o.verified);
  return (
    <div className="stagger" style={{ display: "grid", gap: 20 }}>
      <SectionHead eyebrow="RM · Flow C" title="Xác minh nghĩa vụ"
        sub="Nghĩa vụ seed từ giao dịch có độ tin cậy thấp (<70%). RM xác minh để nâng confidence lên 100% trước khi optimizer ra quyết định." />
      <div style={{ display: "grid", gap: 14 }}>
        <Card pad={false} style={{ overflow: "hidden" }}>
          <div style={{ padding: "16px 20px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div className="h-title">Cần xác minh</div><Badge tone={need.length ? "warn" : "safe"}>{need.length}</Badge>
          </div>
          {need.length ? (
            <table className="tbl">
              <thead><tr><th>Nghĩa vụ</th><th>Loại</th><th className="right">Trả/tháng</th><th>Độ tin cậy</th><th></th></tr></thead>
              <tbody>
                {need.map(o => (
                  <tr key={o.id} className="row-hover">
                    <td><div style={{ fontWeight: 600 }}>{o.merchant}</div><div className="mono" style={{ fontSize: 10.5, color: "var(--ink-3)" }}>{o.id}</div></td>
                    <td><Badge tone="muted">{o.type}</Badge></td>
                    <td className="right num">{RB.fmtVND(o.monthly_payment)}</td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <div style={{ width: 60, height: 5, borderRadius: 3, background: "rgba(255,255,255,0.08)", overflow: "hidden" }}><div style={{ width: o.confidence * 100 + "%", height: "100%", background: "var(--warn)" }} /></div>
                        <span className="num" style={{ fontSize: 12 }}>{Math.round(o.confidence * 100)}%</span>
                      </div>
                    </td>
                    <td className="right"><Btn size="sm" variant="primary" icon="check" onClick={() => actions.verifyObligation(o.id, "rm_bob")}>Xác minh</Btn></td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <Empty icon="check" title="Không còn gì cần xác minh" sub="Mọi nghĩa vụ độ tin cậy thấp đã được xử lý." />}
        </Card>
        {done.length > 0 && (
          <Card style={{ display: "grid", gap: 10 }}>
            <div className="eyebrow">Đã xác minh</div>
            {done.map(o => (
              <div key={o.id} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", fontSize: 13 }}>
                <span style={{ fontWeight: 600 }}>{o.merchant}</span>
                <Badge tone="safe" dot>✓ {o.verified_by} · {new Date(o.verified_at).toLocaleDateString("vi-VN")}</Badge>
              </div>
            ))}
          </Card>
        )}
      </div>
    </div>
  );
}

/* ============ 11. FEEDBACK & OUTCOMES ============ */
function FeedbackScreen({ ctx }) {
  const { state, actions } = ctx;
  const [outcome, setOutcome] = useState("PAID_ON_TIME");
  const [decId, setDecId] = useState(state.outcomePrompt || (state.decisionIds[0] || ""));
  const [note, setNote] = useState("");
  const m = RB.feedbackMetrics(state.outcomes);
  useEffect(() => { if (state.outcomePrompt) setDecId(state.outcomePrompt); }, [state.outcomePrompt]);

  const kpis = [
    ["Tỷ lệ trả đúng hạn", (m.approval_outcome_rate * 100).toFixed(0) + "%", m.approval_outcome_rate >= 0.8 ? "var(--safe)" : "var(--warn)"],
    ["Tỷ lệ trễ", (m.late_rate * 100).toFixed(0) + "%", m.late_rate > 0.1 ? "var(--warn)" : "var(--ink)"],
    ["False-approve", (m.false_approve_rate * 100).toFixed(0) + "%", m.false_approve_rate > 0.1 ? "var(--danger)" : "var(--ink)"],
    ["Tổng outcome", m.total_outcomes, "var(--ink)"],
  ];

  return (
    <div className="stagger" style={{ display: "grid", gap: 20 }}>
      <SectionHead eyebrow="RM · Flow C" title="Feedback & Outcomes"
        sub="Ghi nhận kết quả trả nợ thực tế để đo chất lượng mô hình. Dataset có thể export để huấn luyện."
        right={<Btn icon="arrow" onClick={() => actions.toast("Đã export dataset (" + state.outcomes.length + " dòng) — demo")}>Export dataset</Btn>} />

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 14 }}>
        {kpis.map(([l, v, t]) => <MetricCard key={l} label={l} value={v} tone={t} icon="feedback" />)}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "360px 1fr", gap: 20, alignItems: "start" }}>
        <Card style={{ display: "grid", gap: 14 }}>
          <div className="h-title">Ghi nhận kết quả</div>
          <Field label="Quyết định"><Select value={decId} onChange={setDecId} options={state.decisionIds.length ? state.decisionIds.map(id => ({ value: id, label: id })) : [{ value: "", label: "— chưa có —" }]} /></Field>
          <Field label="Kết quả thực tế"><Select value={outcome} onChange={setOutcome} options={["PAID_ON_TIME", "LATE", "MISSED", "RESTRUCTURED", "DEFAULT"]} /></Field>
          <Field label="Ghi chú"><textarea className="input" rows={3} value={note} onChange={(e) => setNote(e.target.value)} placeholder="Tuỳ chọn…" /></Field>
          <Btn variant="primary" icon="check" disabled={!decId} onClick={() => { actions.recordOutcome({ decision_id: decId, outcome, recorded_by: "rm_bob", note }); setNote(""); }}>Ghi outcome</Btn>
        </Card>

        <Card style={{ display: "grid", gap: 14 }}>
          <div className="h-title">Phân bố kết quả</div>
          <div style={{ display: "grid", gap: 9 }}>
            {Object.entries(m.counts).map(([k, v]) => {
              const pct = m.total_outcomes ? (v / m.total_outcomes) * 100 : 0;
              const tone = k === "PAID_ON_TIME" ? "var(--safe)" : k === "LATE" || k === "RESTRUCTURED" ? "var(--warn)" : "var(--danger)";
              return (
                <div key={k} style={{ display: "grid", gridTemplateColumns: "140px 1fr 34px", alignItems: "center", gap: 10 }}>
                  <span style={{ fontSize: 12.5, color: "var(--ink-2)" }}>{k}</span>
                  <div style={{ height: 8, borderRadius: 5, background: "rgba(255,255,255,0.06)", overflow: "hidden" }}><div style={{ width: pct + "%", height: "100%", background: tone, borderRadius: 5, transition: "width .4s ease" }} /></div>
                  <span className="num" style={{ fontSize: 12.5, textAlign: "right", fontWeight: 600 }}>{v}</span>
                </div>
              );
            })}
          </div>
          <hr className="divider" />
          <div className="eyebrow">Outcome gần đây</div>
          <div style={{ display: "grid", gap: 7, maxHeight: 180, overflowY: "auto" }}>
            {state.outcomes.slice().reverse().slice(0, 8).map(o => (
              <div key={o.id} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", fontSize: 12.5 }}>
                <span style={{ color: "var(--ink-2)" }}>{o.item_name || o.decision_id} · {o.recorded_by}</span>
                <StatusBadge value={o.outcome} dot={false} />
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

/* ============ 12. PORTFOLIO DASHBOARD ============ */
function PortfolioScreen({ ctx }) {
  const s = RB.portfolioSummary();
  const big = [
    ["Khách at-risk", s.at_risk_count, "/ " + s.total_customers + " khách", "var(--danger)", "shield"],
    ["Cảnh báo sớm", s.early_warned_count, "khách được flag", "var(--warn)", "bell"],
    ["Sẵn sàng cross-sell", s.cross_sell_ready_count, "cơ hội", "var(--safe)", "spark"],
    ["Đã đánh giá", s.evaluated_customers, "/ " + s.total_customers + " khách", "var(--info)", "user"],
  ];
  return (
    <div className="stagger" style={{ display: "grid", gap: 20 }}>
      <SectionHead eyebrow="Operator" title="Portfolio — tổng quan rủi ro danh mục"
        sub="Bức tranh toàn danh mục: khách rủi ro, cảnh báo sớm, ước tính nghĩa vụ và NPL tránh được." />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 14 }}>
        {big.map(([l, v, sub, t, ic]) => <MetricCard key={l} label={l} value={RB.fmtNum(v)} sub={sub} tone={t} icon={ic} accent />)}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        <Card style={{ display: "grid", gap: 14, position: "relative", overflow: "hidden" }}>
          <div style={{ position: "absolute", right: -40, top: -40, width: 160, height: 160, borderRadius: "50%", background: "var(--accent-soft)", filter: "blur(20px)" }} />
          <div className="eyebrow" style={{ position: "relative" }}>Tổng nghĩa vụ ước tính (danh mục)</div>
          <div className="num" style={{ fontSize: 38, fontWeight: 700, letterSpacing: "-0.02em", position: "relative" }}>{RB.fmtVND(s.total_estimated_obligation)}</div>
          <div style={{ fontSize: 12.5, color: "var(--ink-3)", position: "relative" }}>Tổng dư nợ nghĩa vụ đang theo dõi của toàn bộ khách đã đánh giá.</div>
        </Card>
        <Card style={{ display: "grid", gap: 14 }}>
          <div className="eyebrow">NPL tránh được (ước tính)</div>
          <div className="num" style={{ fontSize: 38, fontWeight: 700, letterSpacing: "-0.02em", color: "var(--safe)" }}>{RB.fmtVND(s.estimated_npl_avoided)}</div>
          <div className="glass-flat" style={{ padding: 12, fontSize: 12, color: "var(--ink-3)", lineHeight: 1.5, display: "flex", gap: 8 }}>
            <span style={{ color: "var(--warn)", flex: "none" }}><Icon name="info" size={16} /></span>
            <span>NPL avoided là <b style={{ color: "var(--ink-2)" }}>giả định demo</b> dựa trên giả thuyết giảm vỡ nợ rate = {(s.assumed_default_reduction_rate * 100).toFixed(0)}%. Không phải số liệu thực.</span>
          </div>
        </Card>
      </div>
    </div>
  );
}

Object.assign(window, { ConsentAuditScreen, RMReviewScreen, VerifyScreen, FeedbackScreen, PortfolioScreen });
