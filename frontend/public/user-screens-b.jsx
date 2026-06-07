/* ============================================================
   BNPL Assistant — End-user screens (3,4,5)
   ============================================================ */
const __B = window.BNPL;
const { useState } = React;

/* ============ 3. HEALTH DASHBOARD ============ */
function HealthScreen({ ctx }) {
  const { state, actions } = ctx;
  if (!state.profile) return <NoProfile actions={actions} />;
  const a = __B.analyze(state.profile, state.obligations);
  const fc = __B.forecast(state.profile, state.obligations, 6);
  const al = __B.alerts(state.profile, state.obligations, fc).alerts;
  const bandLabel = { SAFE: "An toàn", ACCEPTABLE: "Chấp nhận", WARNING: "Cảnh báo", DANGER: "Nguy hiểm" };

  return (
    <div className="stagger" style={{ display: "grid", gap: 20 }}>
      <SectionHead eyebrow="Bước 3 · Sức khỏe tài chính" title="Dashboard sức khỏe"
        sub={`Hồ sơ ${state.profile.id} · cập nhật theo thời gian thực từ thu nhập, chi tiêu và nghĩa vụ.`}
        right={<Btn icon="cart" variant="primary" onClick={() => actions.go("planning")}>Mô phỏng mua sắm</Btn>} />

      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 14 }}>
        <MetricCard label="NCF · dòng tiền ròng" icon="chart" accent
          value={__B.fmtVND(a.ncf)} tone={a.ncf < 0 ? "var(--danger)" : "var(--ink)"}
          sub="mỗi tháng" />
        <MetricCard label="DTI · tỷ lệ nợ/thu nhập" icon="bolt"
          value={__B.fmtPct(a.dti)} badge={<StatusBadge value={a.dti_band} />} sub={bandLabel[a.dti_band]} />
        <MetricCard label="Tỷ lệ tiết kiệm" icon="heart"
          value={__B.fmtPct(a.saving_rate)} tone={a.saving_rate < 10 ? "var(--warn)" : "var(--ink)"} />
        <MetricCard label="EFR · quỹ khẩn cấp" icon="shield"
          value={a.efr + " th"} sub="tháng chi tiêu" tone={a.efr < 3 ? "var(--warn)" : "var(--ink)"} />
        <MetricCard label="PGRS · rủi ro mục tiêu" icon="grid"
          value={a.pgrs} sub="thang điểm 0–100" tone={a.pgrs >= 70 ? "var(--danger)" : "var(--ink)"} />
      </div>

      {a.flags.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
          <span className="eyebrow" style={{ marginRight: 4 }}>Cờ:</span>
          {a.flags.map(f => <Badge key={f} tone="warn" dot>{f}</Badge>)}
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1.25fr 1fr", gap: 20, alignItems: "start" }}>
        <Card style={{ display: "grid", gap: 14 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div className="h-title">Mục tiêu tài chính</div>
            <Badge tone="muted">{a.goals.length} mục tiêu</Badge>
          </div>
          <table className="tbl">
            <thead><tr><th>Mục tiêu</th><th className="right">Cần thêm</th><th className="right">Phân bổ/th</th><th className="right">Trễ (th)</th><th className="right">GRS</th></tr></thead>
            <tbody>
              {a.goals.map(g => (
                <tr key={g.goal_id} className="row-hover">
                  <td style={{ fontWeight: 600 }}>{g.name}</td>
                  <td className="right num">{__B.fmtVND(g.gap)}</td>
                  <td className="right num">{__B.fmtVND(g.monthly_allocated)}</td>
                  <td className="right num">{g.delay}</td>
                  <td className="right"><Badge tone={g.grs >= 70 ? "danger" : g.grs >= 40 ? "warn" : "safe"}>{g.grs}</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <Card style={{ display: "grid", gap: 12 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div className="h-title" style={{ display: "flex", alignItems: "center", gap: 8 }}><Icon name="bell" size={17} />Cảnh báo sớm</div>
            <Badge tone={al.some(x => x.level === "CRITICAL") ? "danger" : al.length ? "warn" : "safe"}>{al.length}</Badge>
          </div>
          {al.length ? (
            <div style={{ display: "grid", gap: 10 }}>
              {al.map((x, i) => (
                <div key={i} className="glass-flat" style={{ padding: 13, display: "grid", gap: 6, borderLeft: `2.5px solid ${x.level === "CRITICAL" ? "var(--danger)" : "var(--warn)"}` }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <Badge tone={x.level === "CRITICAL" ? "danger" : "warn"} dot>{x.level}</Badge>
                    {x.month && <Badge tone="muted">{x.month}</Badge>}
                    <span className="mono" style={{ fontSize: 10.5, color: "var(--ink-3)", marginLeft: "auto" }}>{x.code}</span>
                  </div>
                  <div style={{ fontSize: 13, lineHeight: 1.45 }}>{x.message}</div>
                  <div style={{ fontSize: 12, color: "var(--ink-3)", lineHeight: 1.4 }}>→ {x.recommendation}</div>
                </div>
              ))}
            </div>
          ) : <Empty icon="check" title="Không có cảnh báo" sub="Tình hình tài chính đang ổn định." />}
        </Card>
      </div>
    </div>
  );
}

/* ============ 4. OBLIGATIONS ============ */
function ObligationsScreen({ ctx }) {
  const { state, actions } = ctx;
  if (!state.profile) return <NoProfile actions={actions} />;
  const [showAdd, setShowAdd] = useState(false);
  const [draft, setDraft] = useState({ type: "BNPL", merchant: "", category: "", principal_amount: 0, monthly_payment: 0, due_day: 1, remaining_terms: 6, apr: 0, status: "ACTIVE" });
  const obs = state.obligations;

  const add = () => {
    if (!draft.merchant) { actions.toast("Nhập tên merchant", "danger"); return; }
    actions.addObligation(draft);
    setDraft({ type: "BNPL", merchant: "", category: "", principal_amount: 0, monthly_payment: 0, due_day: 1, remaining_terms: 6, apr: 0, status: "ACTIVE" });
    setShowAdd(false);
  };

  return (
    <div className="stagger" style={{ display: "grid", gap: 20 }}>
      <SectionHead eyebrow="Bước 4 · Nghĩa vụ" title="Nghĩa vụ đang theo dõi"
        sub="Nghĩa vụ tự seed từ giao dịch CIF có thể có độ tin cậy thấp — cần RM xác minh trước khi ra quyết định."
        right={<Btn icon="plus" onClick={() => setShowAdd(s => !s)}>Thêm thủ công</Btn>} />

      {showAdd && (
        <Card className="fade-in" style={{ display: "grid", gap: 14 }}>
          <div className="h-title">Thêm nghĩa vụ</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12 }}>
            <Field label="Loại"><Select value={draft.type} onChange={(v) => setDraft({ ...draft, type: v })} options={["BNPL", "LOAN", "CREDIT_CARD", "BILL", "SUBSCRIPTION"]} /></Field>
            <Field label="Merchant"><TextInput value={draft.merchant} onChange={(v) => setDraft({ ...draft, merchant: v })} placeholder="VD: Phone Store" /></Field>
            <Field label="Trả/tháng"><MoneyInput value={draft.monthly_payment} onChange={(v) => setDraft({ ...draft, monthly_payment: v || 0 })} /></Field>
            <Field label="Gốc"><MoneyInput value={draft.principal_amount} onChange={(v) => setDraft({ ...draft, principal_amount: v || 0 })} /></Field>
            <Field label="Số kỳ còn lại"><input className="input num" value={draft.remaining_terms} onChange={(e) => setDraft({ ...draft, remaining_terms: +e.target.value.replace(/\D/g, "") || 0 })} /></Field>
            <Field label="APR (%)"><input className="input num" value={draft.apr} onChange={(e) => setDraft({ ...draft, apr: +e.target.value.replace(/[^\d.]/g, "") || 0 })} /></Field>
            <Field label="Ngày đến hạn"><input className="input num" value={draft.due_day} onChange={(e) => setDraft({ ...draft, due_day: +e.target.value.replace(/\D/g, "") || 1 })} /></Field>
            <div style={{ display: "flex", alignItems: "flex-end", gap: 8 }}>
              <Btn variant="primary" onClick={add}>Lưu</Btn>
              <Btn variant="ghost" onClick={() => setShowAdd(false)}>Huỷ</Btn>
            </div>
          </div>
        </Card>
      )}

      <Card pad={false} style={{ overflow: "hidden" }}>
        {obs.length ? (
          <table className="tbl">
            <thead><tr><th>Nghĩa vụ</th><th>Loại</th><th className="right">Trả/tháng</th><th className="right">Kỳ còn lại</th><th>Độ tin cậy</th><th>Trạng thái</th><th></th></tr></thead>
            <tbody>
              {obs.map(o => {
                const needVerify = o.confidence < 0.7 && !o.verified;
                return (
                  <tr key={o.id} className="row-hover">
                    <td><div style={{ fontWeight: 600 }}>{o.merchant}</div><div className="mono" style={{ fontSize: 10.5, color: "var(--ink-3)" }}>{o.id}</div></td>
                    <td><Badge tone="muted">{o.type}</Badge></td>
                    <td className="right num">{__B.fmtVND(o.monthly_payment)}</td>
                    <td className="right num">{o.remaining_terms}</td>
                    <td>
                      {o.verified
                        ? <Badge tone="safe" dot>✓ {o.verified_by}</Badge>
                        : needVerify
                          ? <Badge tone="warn" dot>Cần xác minh · {Math.round(o.confidence * 100)}%</Badge>
                          : <Badge tone="muted">{Math.round(o.confidence * 100)}%</Badge>}
                    </td>
                    <td><StatusBadge value={o.status} /></td>
                    <td className="right"><button className="btn ghost sm" style={{ padding: 7 }} onClick={() => actions.deleteObligation(o.id)} title="Xoá"><Icon name="trash" size={14} /></button></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : <Empty icon="list" title="Chưa có nghĩa vụ" sub="Seed từ CIF (cần consent CIF_TRANSACTIONS) hoặc thêm thủ công."
          action={<Btn icon="bolt" onClick={() => actions.seedObligations()}>Seed từ CIF {state.currentCif}</Btn>} />}
      </Card>
    </div>
  );
}

/* ---- daily Prophet forecast chart ---- */
function DailyForecastChart({ points }) {
  if (!points || !points.length) return <p style={{ fontSize: 13, color: "var(--ink-3)" }}>Chưa có dữ liệu.</p>;
  const W = 720, H = 210, pad = { l: 58, r: 16, t: 14, b: 28 };
  const vals = points.flatMap(p => [p.lower, p.upper, 0]);
  const min = Math.min(...vals), max = Math.max(...vals), span = (max - min) || 1;
  const pw = W - pad.l - pad.r, ph = H - pad.t - pad.b;
  const x = (i) => pad.l + (points.length === 1 ? pw / 2 : (i / (points.length - 1)) * pw);
  const y = (v) => pad.t + ((max - v) / span) * ph;
  const netLine = points.map((p, i) => `${x(i)},${y(p.predicted_net)}`).join(" ");
  const top = points.map((p, i) => `${x(i)},${y(p.upper)}`).join(" ");
  const bot = points.slice().reverse().map((p, i) => `${x(points.length - 1 - i)},${y(p.lower)}`).join(" ");
  const zeroY = y(0);
  const labelIdx = [0, Math.floor(points.length / 3), Math.floor((2 * points.length) / 3), points.length - 1];
  return (
    <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Biểu đồ dự báo theo ngày"
      style={{ width: "100%", height: "auto", display: "block" }}>
      <polygon points={`${top} ${bot}`} fill="var(--accent-soft)" stroke="none" />
      {zeroY >= pad.t && zeroY <= H - pad.b &&
        <line x1={pad.l} x2={W - pad.r} y1={zeroY} y2={zeroY} stroke="var(--danger)" strokeDasharray="4 4" opacity="0.6" />}
      <polyline points={netLine} fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinejoin="round" />
      {labelIdx.map(i => (
        <text key={i} x={x(i)} y={H - 9} textAnchor="middle" className="mono" fill="var(--ink-3)" style={{ fontSize: 10 }}>
          {points[i].date.slice(5)}
        </text>
      ))}
    </svg>
  );
}

/* ============ 5. FORECAST ============ */
function ForecastScreen({ ctx }) {
  const { state, actions } = ctx;
  if (!state.profile) return <NoProfile actions={actions} />;
  const [months, setMonths] = useState(6);
  const fc = __B.forecast(state.profile, state.obligations, months);
  const s = fc.summary;
  const daily = __B.dailyForecast(state.profile, 90);

  return (
    <div className="stagger" style={{ display: "grid", gap: 20 }}>
      <SectionHead eyebrow="Bước 5 · Dự báo" title="Dự báo dòng tiền"
        sub="Số dư cuối kỳ (đường liền) và dòng tiền ròng (đường nét đứt) theo tháng. Đường 0 được nhấn mạnh."
        right={<Segmented value={months} onChange={(v) => setMonths(+v)} options={[{ value: 3, label: "3 th" }, { value: 6, label: "6 th" }, { value: 12, label: "12 th" }]} />} />

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 14 }}>
        <MetricCard label="Dòng tiền ròng 30 ngày" value={__B.fmtVND(s.next_30_net)} tone={s.next_30_net < 0 ? "var(--danger)" : "var(--ink)"} icon="chart" accent />
        <MetricCard label="Dòng tiền ròng 90 ngày" value={__B.fmtVND(s.next_90_net)} tone={s.next_90_net < 0 ? "var(--danger)" : "var(--ink)"} icon="chart" />
        <MetricCard label="Số dư thấp nhất dự kiến" value={__B.fmtVND(s.min_projected_balance)} tone={s.min_projected_balance < 0 ? "var(--danger)" : "var(--ink)"} icon="shield" />
      </div>

      <Card>
        <div className="h-title" style={{ marginBottom: 14 }}>Diễn biến số dư</div>
        <LineChart months={fc.months} />
        <div style={{ display: "flex", gap: 20, marginTop: 10, fontSize: 12, color: "var(--ink-3)" }}>
          <span style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ width: 16, height: 2.5, background: "var(--accent)", borderRadius: 2 }} />Số dư cuối kỳ</span>
          <span style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ width: 16, height: 2.5, background: "var(--accent-2)", borderRadius: 2, opacity: 0.8 }} />Dòng tiền ròng</span>
        </div>
      </Card>

      <Card>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <div className="h-title" style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Icon name="chart" size={18} />Dự báo dòng tiền theo ngày (Prophet)
          </div>
          <div style={{ display: "flex", gap: 6 }}>
            <Badge tone={daily.engine === "prophet" ? "accent" : "muted"}>{daily.engine || "—"}</Badge>
            {daily.history_days > 0 && <Badge tone="muted">{daily.history_days} ngày lịch sử</Badge>}
          </div>
        </div>
        {daily.engine === "prophet" ? (
          <>
            <DailyForecastChart points={daily.points} />
            <div style={{ display: "flex", flexWrap: "wrap", gap: 18, marginTop: 8, fontSize: 12, color: "var(--ink-3)" }}>
              <span><span style={{ display: "inline-block", width: 14, height: 2.5, background: "var(--accent)", borderRadius: 2, verticalAlign: "middle", marginRight: 5 }} />Net/ngày (học mùa vụ theo tuần)</span>
              <span><span style={{ display: "inline-block", width: 12, height: 9, background: "var(--accent-soft)", borderRadius: 2, verticalAlign: "middle", marginRight: 5 }} />Dải tin cậy</span>
              <span>Dự báo {daily.days} ngày · số dư thấp nhất {__B.fmtVND(daily.min_projected_balance)}</span>
            </div>
          </>
        ) : (
          <Empty icon="chart" title="Chưa đủ dữ liệu ngày để dùng Prophet"
            sub="Cần hồ sơ gắn CIF có lịch sử giao dịch theo ngày — hãy chọn Persona A/B (CIF thật) ở sidebar. Hồ sơ nhập tay sẽ dùng dự báo phẳng." />
        )}
      </Card>

      <Card pad={false} style={{ overflow: "hidden" }}>
        <table className="tbl">
          <thead><tr><th>Tháng</th><th className="right">Thu</th><th className="right">Chi</th><th className="right">Trả nợ</th><th className="right">Nghĩa vụ</th><th className="right">Ròng</th><th className="right">Số dư cuối</th><th>Cảnh báo</th></tr></thead>
          <tbody>
            {fc.months.map(m => (
              <tr key={m.month} className="row-hover">
                <td style={{ fontWeight: 600 }}>{m.month}</td>
                <td className="right num">{__B.fmtNum(m.income)}</td>
                <td className="right num">{__B.fmtNum(m.expense)}</td>
                <td className="right num">{__B.fmtNum(m.debt_payment)}</td>
                <td className="right num">{__B.fmtNum(m.obligation_payment)}</td>
                <td className={"right num " + (m.net_cashflow < 0 ? "neg" : "pos")} style={{ fontWeight: 600 }}>{__B.fmtNum(m.net_cashflow)}</td>
                <td className={"right num " + (m.ending_balance < 0 ? "neg" : "")} style={{ fontWeight: 600 }}>{__B.fmtNum(m.ending_balance)}</td>
                <td><div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>{m.warnings.map(w => <Badge key={w} tone={w.includes("NEGATIVE") ? "danger" : "warn"}>{w.replace(/_/g, " ").toLowerCase()}</Badge>)}</div></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

function NoProfile({ actions }) {
  return <Card><Empty icon="user" title="Chưa có hồ sơ" sub="Hãy tạo hồ sơ tài chính trước khi xem màn hình này."
    action={<Btn variant="primary" icon="arrow" onClick={() => actions.go("profile")}>Tạo hồ sơ</Btn>} /></Card>;
}

Object.assign(window, { HealthScreen, ObligationsScreen, ForecastScreen, NoProfile });
