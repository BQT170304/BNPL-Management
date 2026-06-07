/* ============================================================
   BNPL Assistant — shared UI components (glassmorphism)
   ============================================================ */
const { useState, useEffect, useRef, useMemo, useCallback } = React;
const B = window.BNPL;

/* ---- icons (inline, minimal stroke) ---- */
function Icon({ name, size = 18, style }) {
  const s = { width: size, height: size, fill: "none", stroke: "currentColor", strokeWidth: 1.7, strokeLinecap: "round", strokeLinejoin: "round", ...style };
  const P = {
    shield: <path d="M12 3l7 3v5c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3z" />,
    user: <><circle cx="12" cy="8" r="3.5" /><path d="M5 20c0-3.5 3-5.5 7-5.5s7 2 7 5.5" /></>,
    heart: <path d="M12 20s-7-4.3-7-9.3A4.2 4.2 0 0 1 12 7a4.2 4.2 0 0 1 7 3.7c0 5-7 9.3-7 9.3z" />,
    list: <><path d="M8 6h11M8 12h11M8 18h11" /><circle cx="4" cy="6" r="1" /><circle cx="4" cy="12" r="1" /><circle cx="4" cy="18" r="1" /></>,
    chart: <><path d="M4 19V5M4 19h16" /><path d="M7 15l3-4 3 2 4-6" /></>,
    cart: <><circle cx="9" cy="20" r="1.4" /><circle cx="17" cy="20" r="1.4" /><path d="M3 4h2l2.2 11h10l2-7H6" /></>,
    chat: <path d="M5 5h14v10H9l-4 4V5z" />,
    key: <><circle cx="8" cy="12" r="3.5" /><path d="M11.5 12H20M17 12v3M20 12v3" /></>,
    gavel: <><path d="M14 4l6 6-3 3-6-6 3-3zM11 7l-7 7 3 3 7-7M3 21h8" /></>,
    check: <path d="M5 12l4 4 10-10" />,
    feedback: <><path d="M4 5h16v11H8l-4 4V5z" /><path d="M9 10h6M9 13h4" /></>,
    grid: <><rect x="4" y="4" width="7" height="7" rx="1.5" /><rect x="13" y="4" width="7" height="7" rx="1.5" /><rect x="4" y="13" width="7" height="7" rx="1.5" /><rect x="13" y="13" width="7" height="7" rx="1.5" /></>,
    plus: <path d="M12 5v14M5 12h14" />,
    trash: <path d="M5 7h14M10 7V5h4v2M6 7l1 13h10l1-13" />,
    arrow: <path d="M5 12h14M13 6l6 6-6 6" />,
    spark: <path d="M12 3l1.8 5.4L19 10l-5.2 1.6L12 17l-1.8-5.4L5 10l5.2-1.6L12 3z" />,
    info: <><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 8h.01" /></>,
    bolt: <path d="M13 3L5 13h6l-1 8 8-10h-6l1-8z" />,
    send: <path d="M4 12l16-7-7 16-2-7-7-2z" />,
    bell: <><path d="M6 9a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6z" /><path d="M10 19a2 2 0 0 0 4 0" /></>,
    logout: <><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" /></>,
  };
  return <svg viewBox="0 0 24 24" style={s}>{P[name] || null}</svg>;
}

/* ---- Card ---- */
function Card({ children, className = "", style, pad = true, flat = false, ...rest }) {
  return (
    <div className={(flat ? "glass-flat" : "glass") + " " + className}
      style={{ padding: pad ? "calc(20px * var(--pad))" : 0, ...style }} {...rest}>
      {children}
    </div>
  );
}

function SectionHead({ eyebrow, title, sub, right }) {
  return (
    <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: 16, marginBottom: 18 }}>
      <div>
        {eyebrow && <div className="eyebrow" style={{ marginBottom: 7 }}>{eyebrow}</div>}
        <div className="h-display">{title}</div>
        {sub && <div className="h-sub" style={{ marginTop: 6, maxWidth: 620, lineHeight: 1.5 }}>{sub}</div>}
      </div>
      {right}
    </div>
  );
}

/* ---- Badge ---- */
const BAND_TONE = { SAFE: "safe", ACCEPTABLE: "info", WARNING: "warn", DANGER: "danger",
  GRANTED: "safe", ACTIVE: "safe", REVOKED: "muted", EXPIRED: "muted", PAUSED: "warn", CLOSED: "muted",
  CRITICAL: "danger", LOW: "safe", MEDIUM: "warn", HIGH: "danger", VERY_HIGH: "danger",
  PAID_ON_TIME: "safe", LATE: "warn", MISSED: "danger", RESTRUCTURED: "info", DEFAULT: "danger",
  APPROVE: "safe", REJECT: "danger", OVERRIDE: "warn" };
function Badge({ children, tone = "muted", dot = false }) {
  return <span className={"badge " + tone}>{dot && <span className="dot" />}{children}</span>;
}
function StatusBadge({ value, dot = true }) {
  return <Badge tone={BAND_TONE[value] || "muted"} dot={dot}>{value}</Badge>;
}

/* ---- Button ---- */
function Btn({ children, variant = "", size = "", icon, block, ...rest }) {
  return (
    <button className={`btn ${variant} ${size} ${block ? "block" : ""}`} {...rest}>
      {icon && <Icon name={icon} size={size === "sm" ? 15 : 17} />}{children}
    </button>
  );
}

/* ---- Field inputs ---- */
function Field({ label, children, hint }) {
  return (
    <div className="field">
      {label && <label>{label}</label>}
      {children}
      {hint && <span style={{ fontSize: 11.5, color: "var(--ink-3)" }}>{hint}</span>}
    </div>
  );
}
function TextInput({ value, onChange, ...rest }) {
  return <input className="input" value={value ?? ""} onChange={(e) => onChange && onChange(e.target.value)} {...rest} />;
}
function MoneyInput({ value, onChange, big, ...rest }) {
  const display = value === "" || value == null ? "" : B.fmtNum(value);
  return (
    <div style={{ position: "relative" }}>
      <input className={"input num " + (big ? "lg" : "")} inputMode="numeric" value={display}
        onChange={(e) => { const raw = e.target.value.replace(/[^\d]/g, ""); onChange(raw === "" ? "" : parseInt(raw)); }}
        {...rest} />
      <span style={{ position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", color: "var(--ink-3)", fontSize: big ? 18 : 13, pointerEvents: "none", fontWeight: 600 }}>₫</span>
    </div>
  );
}
function Select({ value, onChange, options, ...rest }) {
  return (
    <select className="select" value={value} onChange={(e) => onChange(e.target.value)} {...rest}>
      {options.map((o) => typeof o === "string"
        ? <option key={o} value={o}>{o}</option>
        : <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}
function Segmented({ value, onChange, options }) {
  return (
    <div className="seg">
      {options.map((o) => {
        const v = typeof o === "string" ? o : o.value;
        const l = typeof o === "string" ? o : o.label;
        return <button key={v} className={value === v ? "on" : ""} onClick={() => onChange(v)}>{l}</button>;
      })}
    </div>
  );
}
function Checkbox({ checked, onChange, children }) {
  return (
    <label className="check">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      <span className="box"><Icon name="check" size={13} style={{ stroke: "#0a0712", strokeWidth: 2.6 }} /></span>
      <span style={{ fontSize: 13.5, color: "var(--ink-2)", lineHeight: 1.45 }}>{children}</span>
    </label>
  );
}

/* ---- MetricCard ---- */
function MetricCard({ label, value, sub, tone, badge, icon, accent }) {
  return (
    <Card className="fade-in" style={{ display: "flex", flexDirection: "column", gap: 10, minHeight: 116, position: "relative", overflow: "hidden" }}>
      {accent && <div style={{ position: "absolute", right: -30, top: -30, width: 110, height: 110, borderRadius: "50%", background: "var(--accent-soft)", filter: "blur(12px)" }} />}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", position: "relative" }}>
        <span className="eyebrow">{label}</span>
        {icon && <span style={{ color: "var(--ink-3)" }}><Icon name={icon} size={16} /></span>}
      </div>
      <div className="num" style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em", color: tone || "var(--ink)", position: "relative" }}>{value}</div>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        {badge}
        {sub && <span style={{ fontSize: 12, color: "var(--ink-3)" }}>{sub}</span>}
      </div>
    </Card>
  );
}

/* ---- Line chart (forecast) ---- */
function LineChart({ months, height = 220 }) {
  const W = 720, H = height, padL = 56, padR = 16, padT = 18, padB = 34;
  const [hov, setHov] = useState(null);
  const data = months;
  if (!data.length) return null;
  const vals = data.flatMap(m => [m.ending_balance, m.net_cashflow]);
  const max = Math.max(...vals, 0), min = Math.min(...vals, 0);
  const range = max - min || 1;
  const x = (i) => padL + (i / Math.max(1, data.length - 1)) * (W - padL - padR);
  const y = (v) => padT + (1 - (v - min) / range) * (H - padT - padB);
  const linePath = (key) => data.map((m, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(m[key]).toFixed(1)}`).join(" ");
  const areaPath = "M" + data.map((m, i) => `${x(i).toFixed(1)},${y(m.ending_balance).toFixed(1)}`).join(" L") +
    ` L${x(data.length - 1)},${y(min)} L${x(0)},${y(min)} Z`;
  const zeroY = y(0);
  const fmtAxis = (v) => Math.abs(v) >= 1e6 ? (v / 1e6).toFixed(0) + "tr" : B.fmtNum(v / 1000) + "k";
  const fmtFull = (v) => B.fmtVND(v);

  const TW = 198, TH = 80, TPad = 10;
  const renderTooltip = (i) => {
    const m = data[i];
    const cx = x(i), cy = y(m.ending_balance);
    let tx = cx - TW / 2;
    if (tx < padL) tx = padL;
    if (tx + TW > W - padR) tx = W - padR - TW;
    const ty = cy - TH - 12 < padT ? cy + 16 : cy - TH - 12;
    const rows = [
      ["Số dư cuối tháng", m.ending_balance],
      ["Dòng tiền ròng", m.net_cashflow],
      ...(m.monthly_payment != null ? [["Trả góp/tháng", m.monthly_payment]] : []),
    ];
    const rowH = (TH - TPad * 2 - 16) / rows.length;
    return (
      <g pointerEvents="none">
        <rect x={tx} y={ty} width={TW} height={TH} rx="8" fill="var(--bg0, #1a1225)" stroke="var(--glass-line, rgba(255,255,255,0.12))" strokeWidth="1" opacity="0.97" />
        <text x={tx + TPad} y={ty + TPad + 11} fontSize="11" fontWeight="600" fill="var(--ink, #f0eaf8)">{m.month}</text>
        {rows.map(([label, val], ri) => {
          const ry = ty + TPad + 24 + ri * rowH;
          const tone = label.includes("ròng") ? (val < 0 ? "var(--danger,#f87171)" : "var(--safe,#34d399)") : "var(--accent)";
          return (
            <g key={label}>
              <text x={tx + TPad} y={ry + 11} fontSize="10" fill="var(--ink-3, rgba(240,234,248,0.5))">{label}</text>
              <text x={tx + TW - TPad} y={ry + 11} textAnchor="end" fontSize="10.5" fontWeight="700" fill={tone} className="num">{fmtFull(val)}</text>
            </g>
          );
        })}
      </g>
    );
  };

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height: "auto", display: "block" }} onMouseLeave={() => setHov(null)}>
      <defs>
        <linearGradient id="areaG" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.35" />
          <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
        </linearGradient>
      </defs>
      {[max, (max + min) / 2, min].map((v, i) => (
        <g key={i}>
          <line x1={padL} y1={y(v)} x2={W - padR} y2={y(v)} stroke="rgba(255,255,255,0.07)" />
          <text x={padL - 8} y={y(v) + 4} textAnchor="end" fontSize="10.5" fill="var(--ink-3)" className="num">{fmtAxis(v)}</text>
        </g>
      ))}
      {min < 0 && max > 0 && <line x1={padL} y1={zeroY} x2={W - padR} y2={zeroY} stroke="var(--danger)" strokeOpacity="0.55" strokeDasharray="4 4" />}
      {hov !== null && <line x1={x(hov)} y1={padT} x2={x(hov)} y2={H - padB} stroke="rgba(255,255,255,0.15)" strokeDasharray="3 3" />}
      <path d={areaPath} fill="url(#areaG)" />
      <path d={linePath("ending_balance")} fill="none" stroke="var(--accent)" strokeWidth="2.4" strokeLinejoin="round" strokeLinecap="round" />
      <path d={linePath("net_cashflow")} fill="none" stroke="var(--accent-2)" strokeWidth="2" strokeDasharray="5 4" strokeLinejoin="round" />
      {data.map((m, i) => (
        <g key={i}>
          <circle cx={x(i)} cy={y(m.ending_balance)} r={hov === i ? 5 : 3.2}
            fill="var(--bg0)" stroke="var(--accent)" strokeWidth="2"
            style={{ transition: "r 0.1s", cursor: "pointer" }} />
          <circle cx={x(i)} cy={y(m.ending_balance)} r="14" fill="transparent"
            onMouseEnter={() => setHov(i)} />
          <text x={x(i)} y={H - 12} textAnchor="middle" fontSize="10" fill="var(--ink-3)">{m.month.slice(2)}</text>
        </g>
      ))}
      {hov !== null && renderTooltip(hov)}
    </svg>
  );
}

/* ---- score breakdown bars ---- */
function ScoreBars({ breakdown }) {
  const items = [
    ["Dòng tiền", breakdown.cashflow_safety], ["Áp lực nợ", breakdown.obligation_pressure],
    ["Mục tiêu", breakdown.goal_impact], ["Quỹ k.cấp", breakdown.emergency_fund], ["Chi phí", breakdown.total_cost],
  ];
  return (
    <div style={{ display: "grid", gap: 7 }}>
      {items.map(([l, v]) => (
        <div key={l} style={{ display: "grid", gridTemplateColumns: "78px 1fr 30px", alignItems: "center", gap: 9 }}>
          <span style={{ fontSize: 11, color: "var(--ink-3)" }}>{l}</span>
          <div style={{ height: 6, borderRadius: 4, background: "rgba(255,255,255,0.07)", overflow: "hidden" }}>
            <div style={{ width: v + "%", height: "100%", borderRadius: 4, background: v >= 70 ? "var(--safe)" : v >= 45 ? "var(--warn)" : "var(--danger)" }} />
          </div>
          <span className="num" style={{ fontSize: 11, color: "var(--ink-2)", textAlign: "right" }}>{v}</span>
        </div>
      ))}
    </div>
  );
}

/* ---- score ring ---- */
function ScoreRing({ score, size = 92 }) {
  const r = (size - 12) / 2, c = 2 * Math.PI * r;
  const tone = score >= 75 ? "var(--safe)" : score >= 50 ? "var(--warn)" : "var(--danger)";
  return (
    <div style={{ position: "relative", width: size, height: size, flex: "none" }}>
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="6" />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={tone} strokeWidth="6" strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={c * (1 - score / 100)} style={{ transition: "stroke-dashoffset .6s ease" }} />
      </svg>
      <div style={{ position: "absolute", inset: 0, display: "grid", placeItems: "center" }}>
        <div style={{ textAlign: "center" }}>
          <div className="num" style={{ fontSize: 22, fontWeight: 700, color: tone, lineHeight: 1 }}>{score}</div>
          <div style={{ fontSize: 9, color: "var(--ink-3)", letterSpacing: "0.08em" }}>/100</div>
        </div>
      </div>
    </div>
  );
}

/* ---- empty state ---- */
function Empty({ icon = "info", title, sub, action }) {
  return (
    <div style={{ textAlign: "center", padding: "48px 24px", color: "var(--ink-3)" }}>
      <div style={{ display: "inline-grid", placeItems: "center", width: 56, height: 56, borderRadius: 16, background: "rgba(255,255,255,0.04)", border: "1px solid var(--glass-line)", marginBottom: 16, color: "var(--ink-2)" }}>
        <Icon name={icon} size={24} />
      </div>
      <div className="h-title" style={{ color: "var(--ink-2)", marginBottom: 6 }}>{title}</div>
      {sub && <div style={{ fontSize: 13, maxWidth: 380, margin: "0 auto 16px", lineHeight: 1.5 }}>{sub}</div>}
      {action}
    </div>
  );
}

/* ---- toast ---- */
function useToast() {
  const [toast, setToast] = useState(null);
  const show = useCallback((msg, tone = "accent") => {
    setToast({ msg, tone, id: Math.random() });
    clearTimeout(window.__tt); window.__tt = setTimeout(() => setToast(null), 3200);
  }, []);
  const node = toast ? (
    <div className="fade-in glass" key={toast.id} style={{ position: "fixed", bottom: 26, left: "50%", transform: "translateX(-50%)", zIndex: 9000, padding: "12px 18px", display: "flex", alignItems: "center", gap: 10, boxShadow: "var(--shadow-lg)" }}>
      <span style={{ color: toast.tone === "danger" ? "var(--danger)" : "var(--accent)" }}><Icon name={toast.tone === "danger" ? "info" : "check"} size={17} /></span>
      <span style={{ fontSize: 13.5, fontWeight: 500 }}>{toast.msg}</span>
    </div>
  ) : null;
  return [node, show];
}

Object.assign(window, {
  Icon, Card, SectionHead, Badge, StatusBadge, Btn, Field, TextInput, MoneyInput, Select, Segmented, Checkbox,
  MetricCard, LineChart, ScoreBars, ScoreRing, Empty, useToast, BAND_TONE,
});
