/* ============================================================
   BNPL Assistant — End-user screens (1–7)
   ============================================================ */
const _B = window.BNPL;
const { useState } = React;

/* shared little row-editor */
function RowEditor({ rows, cols, onChange, addLabel, blank }) {
  const set = (i, key, val) => { const next = rows.map((r, j) => j === i ? { ...r, [key]: val } : r); onChange(next); };
  const add = () => onChange([...rows, { ...blank }]);
  const del = (i) => onChange(rows.filter((_, j) => j !== i));
  return (
    <div style={{ display: "grid", gap: 8 }}>
      {rows.map((r, i) => (
        <div key={i} style={{ display: "grid", gridTemplateColumns: cols.map(c => c.w || "1fr").join(" ") + " 36px", gap: 8, alignItems: "center" }}>
          {cols.map((c) => (
            <div key={c.key}>
              {c.type === "money" ? <MoneyInput value={r[c.key]} onChange={(v) => set(i, c.key, v)} />
                : c.type === "select" ? <Select value={r[c.key]} onChange={(v) => set(i, c.key, v)} options={c.options} />
                : c.type === "number" ? <input className="input num" inputMode="numeric" value={r[c.key] ?? ""} onChange={(e) => set(i, c.key, e.target.value === "" ? "" : Number(e.target.value.replace(/[^\d.]/g, "")))} />
                : <TextInput value={r[c.key]} onChange={(v) => set(i, c.key, v)} placeholder={c.ph} />}
            </div>
          ))}
          <button className="btn ghost sm" style={{ padding: 8 }} onClick={() => del(i)} title="Xoá dòng"><Icon name="trash" size={15} /></button>
        </div>
      ))}
      <button className="btn sm" style={{ justifySelf: "start", marginTop: 2 }} onClick={add}><Icon name="plus" size={14} />{addLabel}</button>
    </div>
  );
}

/* ============ 1. CONSENT ============ */
function ConsentScreen({ ctx }) {
  const { state, actions } = ctx;
  const [cif, setCif] = useState(state.currentCif || "100");
  const [scopes, setScopes] = useState(["CIF_SUMMARY", "CIF_TRANSACTIONS"]);
  const [grantedBy, setGrantedBy] = useState("user-self");
  const [ttl, setTtl] = useState(90);
  const [confirm, setConfirm] = useState(false);
  const existing = state.consents.find(c => c.cif === cif && c.status === "GRANTED");
  const seed = existing ? _B.SEED[cif] : null;

  const toggleScope = (s) => setScopes(p => p.includes(s) ? p.filter(x => x !== s) : [...p, s]);

  return (
    <div className="stagger" style={{ display: "grid", gap: 20 }}>
      <SectionHead eyebrow="Bước 1 · Flow A" title="Chọn & cấp quyền dữ liệu CIF"
        sub="Consent là cổng chặn: mọi truy cập dữ liệu ngân hàng (số liệu mồi, nghĩa vụ) đều yêu cầu cấp quyền trước. Chưa cấp → backend trả 403 CONSENT_REQUIRED." />
      <div style={{ display: "grid", gridTemplateColumns: "1.1fr 0.9fr", gap: 20, alignItems: "start" }}>
        <Card style={{ display: "grid", gap: 18 }}>
          <Field label="Mã CIF (ngân hàng)">
            <Select value={cif} onChange={(v) => setCif(v)} options={_B.CIFS.map(c => ({ value: c, label: `CIF ${c} · ${_B.SEED[c].subject}` }))} />
          </Field>
          <Field label="Phạm vi truy cập (scopes)">
            <div style={{ display: "grid", gap: 10, marginTop: 2 }}>
              <Checkbox checked={scopes.includes("CIF_SUMMARY")} onChange={() => toggleScope("CIF_SUMMARY")}>
                <b style={{ color: "var(--ink)" }}>CIF_SUMMARY</b> — số liệu tổng hợp (thu nhập, chi tiêu, trả nợ) để prefill hồ sơ
              </Checkbox>
              <Checkbox checked={scopes.includes("CIF_TRANSACTIONS")} onChange={() => toggleScope("CIF_TRANSACTIONS")}>
                <b style={{ color: "var(--ink)" }}>CIF_TRANSACTIONS</b> — lịch sử giao dịch để gợi ý nghĩa vụ định kỳ
              </Checkbox>
            </div>
          </Field>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
            <Field label="Cấp bởi (granted_by)"><TextInput value={grantedBy} onChange={setGrantedBy} /></Field>
            <Field label="Hiệu lực (ngày)"><input className="input num" inputMode="numeric" value={ttl} onChange={(e) => setTtl(e.target.value.replace(/[^\d]/g, ""))} /></Field>
          </div>
          <hr className="divider" />
          <Checkbox checked={confirm} onChange={setConfirm}>
            Tôi xác nhận đồng ý cho phép BNPL Assistant truy cập dữ liệu của CIF {cif} trong phạm vi đã chọn.
          </Checkbox>
          <div style={{ display: "flex", gap: 10 }}>
            <Btn variant="primary" icon="key" disabled={!confirm || !scopes.length}
              onClick={() => actions.grantConsent({ cif, scopes, granted_by: grantedBy, ttl_days: ttl ? +ttl : null, subject: _B.SEED[cif].subject })}>
              Cấp quyền
            </Btn>
            {existing && <Btn variant="danger" onClick={() => actions.revokeConsent(existing.consent_id)}>Thu hồi</Btn>}
          </div>
        </Card>

        <Card style={{ display: "grid", gap: 16 }}>
          <div className="eyebrow">Trạng thái</div>
          {existing ? (
            <>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <StatusBadge value="GRANTED" />
                <span style={{ fontSize: 13.5, fontWeight: 600 }}>Đã cấp quyền cho CIF {cif}</span>
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {existing.scopes.map(s => <span key={s} className="chip mono">{s}</span>)}
              </div>
              <div style={{ fontSize: 12, color: "var(--ink-3)" }} className="mono">consent_id: {existing.consent_id}</div>
              <hr className="divider" />
              <div className="eyebrow">Số liệu mồi (GET /seed)</div>
              <div style={{ display: "grid", gap: 8 }}>
                {[["Thu nhập", seed.income], ["Chi tiêu", seed.expense], ["Trả nợ/tháng", seed.debt_payment]].map(([l, v]) => (
                  <div key={l} style={{ display: "flex", justifyContent: "space-between", fontSize: 13.5 }}>
                    <span style={{ color: "var(--ink-2)" }}>{l}</span><span className="num" style={{ fontWeight: 600 }}>{_B.fmtVND(v)}</span>
                  </div>
                ))}
              </div>
              <Btn variant="primary" block icon="arrow" onClick={() => { actions.setCif(cif); actions.go("profile"); }}>Dùng dữ liệu → Tạo hồ sơ</Btn>
            </>
          ) : (
            <Empty icon="key" title="Chưa cấp quyền" sub={`Dữ liệu của CIF ${cif} đang bị khoá. Cấp quyền để mở khoá số liệu mồi và gợi ý nghĩa vụ.`} />
          )}
        </Card>
      </div>
    </div>
  );
}

/* ============ 2. PROFILE ============ */
function ProfileScreen({ ctx }) {
  const { state, actions } = ctx;
  const [p, setP] = useState(() => state.profile ? structuredClone(state.profile) : _B.defaultProfile());
  const upd = (patch) => setP(prev => ({ ...prev, ...patch }));
  const updIncome = (k, v) => setP(prev => ({ ...prev, income: { ...prev.income, [k]: v === "" ? 0 : v } }));
  const consent = state.consents.find(c => c.cif === state.currentCif && c.status === "GRANTED");
  const canSeedOblig = consent && consent.scopes.includes("CIF_TRANSACTIONS");
  const t = _B.totals(p);

  const prefill = () => {
    if (!consent) return;
    const seed = _B.SEED[state.currentCif];
    upd({ income: { ...p.income, salary: seed.income } });
    actions.toast(`Đã prefill thu nhập từ CIF ${state.currentCif}`);
  };

  return (
    <div className="stagger" style={{ display: "grid", gap: 20 }}>
      <SectionHead eyebrow="Bước 2 · Hồ sơ tài chính" title="Tạo hồ sơ tài chính"
        sub="Form chính của Flow A/B. Có thể prefill từ CIF (cần consent) hoặc nhập tay. Số dương = vào, dùng để tính NCF, DTI, EFR ở bước sau."
        right={consent && <Btn icon="bolt" onClick={prefill}>Prefill từ CIF {state.currentCif}</Btn>} />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 20, alignItems: "start" }}>
        <div style={{ display: "grid", gap: 18 }}>
          <Card style={{ display: "grid", gap: 16 }}>
            <div className="h-title">Thu nhập hàng tháng</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
              <Field label="Lương (salary)"><MoneyInput value={p.income.salary} onChange={(v) => updIncome("salary", v)} /></Field>
              <Field label="Thu nhập phụ (secondary)"><MoneyInput value={p.income.secondary} onChange={(v) => updIncome("secondary", v)} /></Field>
              <Field label="Thưởng TB/tháng"><MoneyInput value={p.income.avg_bonus_monthly} onChange={(v) => updIncome("avg_bonus_monthly", v)} /></Field>
              <Field label="Thu nhập thụ động"><MoneyInput value={p.income.passive} onChange={(v) => updIncome("passive", v)} /></Field>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
              <Field label="Khẩu vị rủi ro (risk)"><Select value={p.risk} onChange={(v) => upd({ risk: v })} options={["LOW", "MEDIUM", "HIGH"]} /></Field>
              <Field label="Quỹ khẩn cấp (emergency_fund)"><MoneyInput value={p.emergency_fund} onChange={(v) => upd({ emergency_fund: v || 0 })} /></Field>
            </div>
          </Card>

          <Card style={{ display: "grid", gap: 14 }}>
            <div className="h-title">Chi tiêu</div>
            <RowEditor rows={p.expenses} onChange={(r) => upd({ expenses: r })} addLabel="Thêm chi tiêu"
              blank={{ category: "", amount: 0, classification: "FIXED" }}
              cols={[{ key: "category", ph: "Hạng mục", w: "1.4fr" }, { key: "amount", type: "money" }, { key: "classification", type: "select", options: ["FIXED", "SEMI_FIXED", "DISCRETIONARY"] }]} />
          </Card>

          <Card style={{ display: "grid", gap: 14 }}>
            <div className="h-title">Khoản nợ hiện có</div>
            <RowEditor rows={p.debts} onChange={(r) => upd({ debts: r })} addLabel="Thêm khoản nợ"
              blank={{ name: "", monthly_payment: 0, balance: 0, apr: 0, months_remaining: 0, debt_type: "INSTALLMENT" }}
              cols={[{ key: "name", ph: "Tên", w: "1.3fr" }, { key: "monthly_payment", type: "money" }, { key: "balance", type: "money" }, { key: "debt_type", type: "select", options: ["REVOLVING", "INSTALLMENT", "SECURED"] }]} />
          </Card>

          <Card style={{ display: "grid", gap: 14 }}>
            <div className="h-title">Tài sản</div>
            <RowEditor rows={p.assets} onChange={(r) => upd({ assets: r })} addLabel="Thêm tài sản"
              blank={{ type: "CASH", value: 0, liquidity: "HIGH" }}
              cols={[{ key: "type", type: "select", options: ["CASH", "SAVINGS", "OTHER"] }, { key: "value", type: "money" }, { key: "liquidity", type: "select", options: ["HIGH", "MEDIUM", "LOW"] }]} />
          </Card>

          <Card style={{ display: "grid", gap: 14 }}>
            <div className="h-title">Mục tiêu tài chính</div>
            <RowEditor rows={p.goals} onChange={(r) => upd({ goals: r })} addLabel="Thêm mục tiêu"
              blank={{ id: _B.uid("g"), name: "", target_amount: 0, deadline: "2030-01-01", priority: "MEDIUM", savings_allocated: 0 }}
              cols={[{ key: "name", ph: "Tên mục tiêu", w: "1.3fr" }, { key: "target_amount", type: "money" }, { key: "savings_allocated", type: "money" }, { key: "priority", type: "select", options: ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"] }]} />
          </Card>
        </div>

        <div style={{ position: "sticky", top: 0, display: "grid", gap: 16 }}>
          <Card style={{ display: "grid", gap: 12 }}>
            <div className="eyebrow">Tóm tắt tự tính</div>
            {[["Tổng thu nhập", t.income, "pos"], ["Tổng chi tiêu", t.expense], ["Trả nợ/tháng", t.debt]].map(([l, v, c]) => (
              <div key={l} style={{ display: "flex", justifyContent: "space-between", fontSize: 13.5 }}>
                <span style={{ color: "var(--ink-2)" }}>{l}</span><span className={"num " + (c || "")} style={{ fontWeight: 600 }}>{_B.fmtVND(v)}</span>
              </div>
            ))}
            <hr className="divider" />
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 14 }}>
              <span style={{ fontWeight: 600 }}>NCF ước tính</span>
              <span className={"num " + ((t.income - t.expense - t.debt) < 0 ? "neg" : "pos")} style={{ fontWeight: 700 }}>{_B.fmtVND(t.income - t.expense - t.debt)}</span>
            </div>
          </Card>
          <Btn variant="primary" block icon="check" onClick={() => { actions.saveProfile(p); actions.go("health"); }}>Lưu hồ sơ & xem sức khỏe</Btn>
          {canSeedOblig
            ? <Btn block icon="bolt" onClick={() => { actions.saveProfile(p); actions.seedObligations(); }}>Seed nghĩa vụ từ CIF {state.currentCif}</Btn>
            : <div style={{ fontSize: 12, color: "var(--ink-3)", textAlign: "center", lineHeight: 1.5 }}>Cần consent CIF_TRANSACTIONS để seed nghĩa vụ tự động.</div>}
        </div>
      </div>
    </div>
  );
}

window.__USER_SCREENS_1_2 = { ConsentScreen, ProfileScreen, RowEditor };
Object.assign(window, { ConsentScreen, ProfileScreen, RowEditor });
