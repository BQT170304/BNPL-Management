/* ============================================================
   BNPL Assistant — Planning (center) + Copilot (6,7)
   ============================================================ */
const ___B = window.BNPL;
const { useState, useEffect, useRef } = React;

/* ============ 6. PLANNING — Mô phỏng & Khuyến nghị ============ */
function PlanningScreen({ ctx }) {
  const { state, actions } = ctx;
  if (!state.profile) return <NoProfile actions={actions} />;
  const [item, setItem] = useState("Điện thoại");
  const [amount, setAmount] = useState(15000000);
  const [horizon, setHorizon] = useState(6);
  const [open, setOpen] = useState(false);
  const [apr, setApr] = useState(0);
  const [fee, setFee] = useState(0);
  const [lateFee, setLateFee] = useState(0);
  const [subsidy, setSubsidy] = useState(0);
  const [tenor, setTenor] = useState("");
  const [result, setResult] = useState(null);
  const [explain, setExplain] = useState(null);

  const [busy, setBusy] = useState(false);
  const run = async (createDecision) => {
    const input = { profile_id: state.profile.id, item_name: item, amount: amount || 0, horizon_months: horizon,
      apr: +apr || 0, fee: +fee || 0, late_fee: +lateFee || 0, merchant_subsidy: +subsidy || 0, tenor: tenor ? +tenor : undefined };
    setBusy(true);
    try {
      const rec = await ___B.recommend(state.profile, state.obligations, input, createDecision, state.store);
      setResult(rec); setExplain(null);
      if (createDecision && rec.decision_id) { actions.registerDecision(rec.decision_id); actions.toast("Đã tạo quyết định " + rec.decision_id); }
      else if (!createDecision) { actions.toast("Đã mô phỏng nhanh " + rec.scenarios.length + " kịch bản (không lưu quyết định)"); }
    } catch (e) { actions.toast("Khuyến nghị lỗi: " + e.message, "danger"); }
    finally { setBusy(false); }
  };
  const doExplain = async () => {
    if (!result || !result.decision_id) return;
    try { setExplain(await ___B.explain(result.decision_id)); }
    catch (e) { actions.toast("Giải thích lỗi: " + e.message, "danger"); }
  };

  const best = result && result.scenarios.find(s => s.scenario.scenario_id === result.best_scenario_id);
  const focus = result
    ? (best
        || result.scenarios.find(s => s.scenario.duration_months === horizon)
        || result.scenarios[0])
    : null;

  return (
    <div className="stagger" style={{ display: "grid", gap: 20 }}>
      <SectionHead eyebrow="Bước 6 · Màn hình trung tâm" title="Mô phỏng & khuyến nghị trả góp"
        sub="Nhập khoản mua, hệ thống chạy optimizer xác định (deterministic) so sánh các kịch bản: trả thẳng, BNPL 3/6/12 tháng, trả trước 30%, hoãn 1 tháng." />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18, alignItems: "end" }}>
        <Card style={{ display: "grid", gap: 16 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 14 }}>
            <Field label="Tên sản phẩm"><TextInput value={item} onChange={setItem} placeholder="VD: Điện thoại" /></Field>
            <Field label="Số tiền"><MoneyInput value={amount} onChange={(v) => setAmount(v || 0)} big /></Field>
          </div>
          <Field label={`Kỳ hạn mong muốn: ${horizon} tháng`}>
            <input type="range" min="1" max="24" value={horizon} onChange={(e) => setHorizon(+e.target.value)}
              style={{ width: "100%", accentColor: "var(--accent)" }} />
          </Field>
          <div>
            <button className="btn ghost sm" style={{ paddingLeft: 0 }} onClick={() => setOpen(o => !o)}>
              <Icon name={open ? "info" : "plus"} size={14} />Điều khoản tài chính (APR / phí / trợ giá){open ? " ▲" : " ▼"}
            </button>
            {open && (
              <div className="fade-in" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginTop: 10 }}>
                <Field label="APR (%/năm)"><input className="input num" value={apr} onChange={(e) => setApr(e.target.value.replace(/[^\d.]/g, ""))} /></Field>
                <Field label="Phí 1 lần"><MoneyInput value={fee} onChange={(v) => setFee(v || 0)} /></Field>
                <Field label="Phí trễ hạn"><MoneyInput value={lateFee} onChange={(v) => setLateFee(v || 0)} /></Field>
                <Field label="NCC trợ giá"><MoneyInput value={subsidy} onChange={(v) => setSubsidy(v || 0)} /></Field>
                <Field label="Kỳ hạn BNPL tuỳ chỉnh (tenor)"><input className="input num" value={tenor} placeholder="vd 9" onChange={(e) => setTenor(e.target.value.replace(/\D/g, ""))} /></Field>
              </div>
            )}
          </div>
          <div style={{ display: "flex", gap: 10 }}>
            <Btn variant="primary" icon="spark" onClick={() => run(true)}>Khuyến nghị & lưu quyết định</Btn>
            <Btn icon="chart" onClick={() => run(false)}>Mô phỏng dòng tiền</Btn>
          </div>
        </Card>

        {best ? (
          <Card className="fade-in" style={{ display: "grid", gap: 14, position: "relative", overflow: "hidden", border: "1px solid oklch(0.70 0.17 var(--accent-h) / 0.4)" }}>
            <div style={{ position: "absolute", inset: 0, background: "var(--accent-soft)", opacity: 0.5, pointerEvents: "none" }} />
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", position: "relative" }}>
              <div>
                <Badge tone={best.blocked ? "warn" : "accent"} dot>{best.blocked ? "Ít rủi ro nhất" : "Khuyến nghị"}</Badge>
                <div className="h-title" style={{ marginTop: 10 }}>{best.scenario.label}</div>
                <div style={{ fontSize: 12.5, color: "var(--ink-2)", marginTop: 4 }}>cho {result.item_name} · {___B.fmtVND(result.amount)}</div>
              </div>
              <ScoreRing score={best.score} />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, position: "relative" }}>
              <div className="glass-flat" style={{ padding: 12 }}><div className="eyebrow">Trả/tháng</div><div className="num" style={{ fontSize: 19, fontWeight: 700, marginTop: 4 }}>{___B.fmtVND(best.scenario.monthly_payment)}</div></div>
              <div className="glass-flat" style={{ padding: 12 }}><div className="eyebrow">Tổng chi phí</div><div className="num" style={{ fontSize: 19, fontWeight: 700, marginTop: 4 }}>{___B.fmtVND(best.scenario.cost.total_cost)}</div></div>
            </div>
            <div style={{ display: "flex", gap: 10, position: "relative" }}>
              <Btn variant="primary" size="sm" icon="info" onClick={doExplain}>Vì sao?</Btn>
              {result.decision_id && <Btn size="sm" icon="gavel" onClick={() => actions.openDecision(result.decision_id)}>Mở RM Review</Btn>}
            </div>
          </Card>
        ) : <Card style={{ display: "grid", placeItems: "center", minHeight: 220 }}><Empty icon="spark" title="Chưa có khuyến nghị" sub="Nhập khoản mua và nhấn Khuyến nghị để xem kịch bản tối ưu." /></Card>}
      </div>

      {focus && (
        <Card className="fade-in" style={{ display: "grid", gap: 12 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div className="h-title" style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <Icon name="chart" size={18} />Dòng tiền dự kiến nếu mua · {focus.scenario.label}
            </div>
            <Badge tone={focus.scenario.forecast.some(m => m.ending_balance < 0) ? "danger" : "safe"}>
              {focus.scenario.forecast.some(m => m.ending_balance < 0) ? "Có tháng âm tiền" : "Số dư an toàn"}
            </Badge>
          </div>
          <LineChart months={focus.scenario.forecast} />
          <div style={{ display: "flex", flexWrap: "wrap", gap: 20, fontSize: 12.5, color: "var(--ink-2)" }}>
            <span>Trả/tháng: <b className="num">{___B.fmtVND(focus.scenario.monthly_payment)}</b></span>
            <span>Số dư thấp nhất: <b className="num">{___B.fmtVND(Math.min(...focus.scenario.forecast.map(m => m.ending_balance)))}</b></span>
            <span>Tổng chi phí: <b className="num">{___B.fmtVND(focus.scenario.cost.total_cost)}</b></span>
          </div>
          <div style={{ fontSize: 11.5, color: "var(--ink-4)", lineHeight: 1.45 }}>
            Dự báo 6 tháng nếu mua theo phương án này — dùng engine forecast (Prophet khi hồ sơ
            gắn CIF có lịch sử) cộng khoản trả góp mới.
          </div>
        </Card>
      )}

      {result && result.advisories.length > 0 && (
        <div className="glass-flat fade-in" style={{ padding: 14, borderLeft: "2.5px solid var(--warn)", display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ color: "var(--warn)" }}><Icon name="info" size={18} /></span>
          <div style={{ fontSize: 13 }}>Có nghĩa vụ cần xác minh: <b>{result.low_confidence_obligations.join(", ")}</b>. Độ tin cậy tối thiểu {result.min_confidence}.
            <span style={{ marginLeft: 8 }}>{result.advisories.map(a => <span key={a} className="chip" style={{ marginLeft: 4 }}>{a}</span>)}</span>
          </div>
        </div>
      )}

      {explain && (
        <Card className="fade-in" style={{ display: "grid", gap: 12, borderLeft: "2.5px solid var(--accent)" }}>
          <div className="h-title" style={{ display: "flex", alignItems: "center", gap: 8 }}><Icon name="info" size={18} />Giải thích quyết định (XAI)</div>
          <div style={{ fontSize: 13.5, color: "var(--ink-2)" }}>{explain.summary}</div>
          <div style={{ display: "grid", gap: 7 }}>
            {explain.key_reasons.map((r, i) => (
              <div key={i} style={{ display: "flex", gap: 9, fontSize: 13, alignItems: "flex-start" }}>
                <span style={{ color: "var(--accent)", marginTop: 2 }}><Icon name="check" size={14} /></span><span>{r}</span>
              </div>
            ))}
          </div>
          {explain.counterfactuals.length > 0 && (
            <div style={{ fontSize: 12.5, color: "var(--ink-3)", lineHeight: 1.5, borderTop: "1px solid var(--glass-line)", paddingTop: 10 }}>
              <b style={{ color: "var(--ink-2)" }}>Phản chứng: </b>{explain.counterfactuals.join(" ")}
            </div>
          )}
        </Card>
      )}

      {result && (
        <Card pad={false} style={{ overflow: "hidden" }}>
          <div style={{ padding: "16px 20px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div className="h-title">So sánh kịch bản</div>
            <span style={{ fontSize: 12, color: "var(--ink-3)" }}>{result.scenarios.length} kịch bản · sắp theo điểm</span>
          </div>
          <table className="tbl">
            <thead><tr><th>Kịch bản</th><th className="right">Trả/tháng</th><th className="right">Tổng chi phí</th><th className="right">Lãi</th><th className="right">Hoà vốn</th><th className="right">DTI sau</th><th className="right">Điểm</th><th>Trạng thái</th></tr></thead>
            <tbody>
              {result.scenarios.map(s => (
                <tr key={s.scenario.scenario_id} className={"row-hover " + (s.blocked ? "dim" : "")}>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      {s.recommended && <span style={{ color: "var(--accent)" }}><Icon name="spark" size={14} /></span>}
                      <span style={{ fontWeight: 600 }}>{s.scenario.label}</span>
                    </div>
                    {s.scenario.upfront_payment > 0 && <span className="mono" style={{ fontSize: 10.5, color: "var(--ink-3)" }}>trả trước {___B.fmtNum(s.scenario.upfront_payment)}</span>}
                  </td>
                  <td className="right num">{___B.fmtVND(s.scenario.monthly_payment)}</td>
                  <td className="right num">{___B.fmtVND(s.scenario.cost.total_cost)}</td>
                  <td className="right num">{___B.fmtVND(s.scenario.cost.total_interest)}</td>
                  <td className="right num">{s.scenario.cost.break_even_month}</td>
                  <td className="right num">{s.scenario.metrics.max_dti}%</td>
                  <td className="right"><span className="num" style={{ fontWeight: 700, color: s.score >= 75 ? "var(--safe)" : s.score >= 50 ? "var(--warn)" : "var(--danger)" }}>{s.score}</span></td>
                  <td>{s.blocked ? <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>{s.reason_codes.map(r => <Badge key={r} tone="danger">{r.replace(/_/g, " ").toLowerCase()}</Badge>)}</div> : s.recommended ? <Badge tone="accent" dot>Đề xuất</Badge> : <Badge tone="muted">khả thi</Badge>}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {best && <div style={{ padding: 18, borderTop: "1px solid var(--glass-line)" }}>
            <div className="eyebrow" style={{ marginBottom: 12 }}>Điểm thành phần · {best.scenario.label}</div>
            <div style={{ maxWidth: 460 }}><ScoreBars breakdown={best.score_breakdown} /></div>
          </div>}
        </Card>
      )}
    </div>
  );
}

/* ============ 7. COPILOT ============ */
function CopilotScreen({ ctx }) {
  const { state, actions } = ctx;
  const [input, setInput] = useState("");
  const scroller = useRef(null);
  const msgs = state.copilotMsgs;
  const suggestions = ["Tôi có nên mua điện thoại 20 triệu trả góp 6 tháng?", "Xem dự báo dòng tiền", "Có cảnh báo gì không?", "Liệt kê nghĩa vụ của tôi"];

  useEffect(() => { if (scroller.current) scroller.current.scrollTop = scroller.current.scrollHeight; }, [msgs.length]);

  const send = (text) => {
    const t = (text ?? input).trim();
    if (!t) return;
    actions.sendCopilot(t);
    setInput("");
  };

  return (
    <div className="stagger" style={{ display: "grid", gap: 20, height: "100%" }}>
      <SectionHead eyebrow="Bước 7 · Trợ lý" title="Copilot hội thoại"
        sub="Hỏi tự nhiên — Copilot gọi optimizer thật (recommend / forecast / alerts / obligations) và trả về tool đã dùng, decision_id, câu hỏi gợi ý." />

      <Card pad={false} style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 460, overflow: "hidden" }}>
        <div ref={scroller} style={{ flex: 1, overflowY: "auto", padding: 22, display: "grid", gap: 14, alignContent: "start" }}>
          {msgs.length === 0 && (
            <div style={{ margin: "auto", textAlign: "center", maxWidth: 440 }}>
              <div style={{ display: "inline-grid", placeItems: "center", width: 56, height: 56, borderRadius: 18, background: "var(--accent-soft)", color: "var(--accent)", marginBottom: 14 }}><Icon name="chat" size={26} /></div>
              <div className="h-title">Bạn cần hỗ trợ gì?</div>
              <div style={{ fontSize: 13, color: "var(--ink-3)", marginTop: 6 }}>Thử một trong các câu hỏi gợi ý bên dưới.</div>
            </div>
          )}
          {msgs.map((m, i) => (
            <div key={i} className="fade-in" style={{ display: "flex", justifyContent: m.role === "user" ? "flex-end" : "flex-start" }}>
              <div className={m.role === "user" ? "" : "glass-flat"} style={{
                maxWidth: "78%", padding: "12px 15px", borderRadius: 16, fontSize: 13.5, lineHeight: 1.5,
                background: m.role === "user" ? "linear-gradient(180deg, var(--accent), var(--accent-strong))" : undefined,
                color: m.role === "user" ? "#0a0712" : "var(--ink)", fontWeight: m.role === "user" ? 500 : 400,
                borderBottomRightRadius: m.role === "user" ? 5 : 16, borderBottomLeftRadius: m.role === "user" ? 16 : 5,
              }}>
                <div>{m.text}</div>
                {m.meta && (
                  <div style={{ marginTop: 10, display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center" }}>
                    <span className="chip" style={{ fontSize: 10.5 }}>tool: {m.meta.tool}</span>
                    {m.meta.used_optimizer && <span className="chip" style={{ fontSize: 10.5, color: "var(--accent)" }}>optimizer</span>}
                    {m.meta.decision_id && <Btn size="sm" icon="gavel" onClick={() => { actions.registerDecision(m.meta.decision_id); actions.openDecision(m.meta.decision_id); }}>Xem quyết định</Btn>}
                  </div>
                )}
                {m.meta && m.meta.follow_up && <div style={{ marginTop: 8, fontSize: 12, color: "var(--ink-3)", fontStyle: "italic" }}>{m.meta.follow_up}</div>}
              </div>
            </div>
          ))}
        </div>

        <div style={{ borderTop: "1px solid var(--glass-line)", padding: 16, display: "grid", gap: 12 }}>
          {msgs.length === 0 && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {suggestions.map(s => <button key={s} className="chip" style={{ cursor: "pointer" }} onClick={() => send(s)}>{s}</button>)}
            </div>
          )}
          <div style={{ display: "flex", gap: 10 }}>
            <input className="input" placeholder="Nhập câu hỏi…" value={input}
              onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()} />
            <Btn variant="primary" icon="send" onClick={() => send()}>Gửi</Btn>
          </div>
        </div>
      </Card>
    </div>
  );
}

Object.assign(window, { PlanningScreen, CopilotScreen });
