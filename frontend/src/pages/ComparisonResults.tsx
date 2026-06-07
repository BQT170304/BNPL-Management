import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  ReferenceLine, Cell,
} from 'recharts';
import { simulatePurchase } from '../api/endpoints';
import type { EvaluateOut, OptionScoreOut, ScenarioSimulationOut } from '../api/types';
import './pages.css';
import './ComparisonResults.css';

const fmt = (n: number) => n >= 1_000_000
  ? `${(n / 1_000_000).toFixed(1)}M ₫`
  : `${n.toLocaleString('vi-VN')} ₫`;

const PLAN_NAMES: Record<string, string> = {
  'full':          'Trả thẳng 1 lần',
  'pay_in_full':   'Trả thẳng 1 lần',
  'PAY_IN_FULL':   'Trả thẳng 1 lần',
  'installment_1': 'Trả thẳng 1 lần',
  'installment_3': 'Trả góp 3 tháng',
  'installment_6': 'Trả góp 6 tháng',
  'installment_12':'Trả góp 12 tháng',
};

const FLAG_VI: Record<string, string> = {
  'NEGATIVE_CASHFLOW':        'Dòng tiền âm',
  'REQUIRES_EMERGENCY_FUND':  'Cần bổ sung quỹ dự phòng',
  'EMERGENCY_FUND_DEPLETED':  'Quỹ dự phòng không đủ',
  'HIGH_DTI':                 'Tỷ lệ nợ cao',
  'DTI_EXCEEDS_LIMIT':        'Nợ vượt ngưỡng an toàn',
  'NEGATIVE_NCF':             'Dòng tiền tháng âm',
  'NCF_CRITICAL':             'Dòng tiền rất thấp',
  'LOW_SAVING':               'Tỷ lệ tiết kiệm thấp',
  'HIGH_RISK':                'Rủi ro tài chính cao',
  'DELAYS_GOALS':             'Ảnh hưởng tiến độ mục tiêu',
  'GOAL_AT_RISK':             'Mục tiêu tài chính bị đe dọa',
};

interface CandidatePlan {
  label: string;
  type: 'PAY_IN_FULL' | 'INSTALLMENT';
  months: number | null;
  apr: number;
}

interface LocationState {
  result: EvaluateOut;
  item_name: string;
  purchase_amount: number;
  profile_id: string;
  cif: string;
  candidate_plans: CandidatePlan[];
}

function translateFlag(flag: string) {
  return FLAG_VI[flag] ?? flag.toLowerCase().replace(/_/g, ' ');
}

function getPlanName(id: string) {
  return PLAN_NAMES[id] ?? PLAN_NAMES[id.toLowerCase()] ?? id.replace(/_/g, ' ');
}

function getInstallMonths(option_id: string): number {
  const m = option_id.match(/(\d+)$/);
  return m ? parseInt(m[1]) : 0;
}

function CashFlowChart({ sim }: { sim: ScenarioSimulationOut }) {
  // Label months as MM/YYYY, trim trailing near-zero-only forecast months
  const raw = sim.months.map(m => ({
    label: m.year_month.slice(5) + '/' + m.year_month.slice(0, 4),
    ncf: m.net_cashflow,
    is_bnpl: m.bnpl_payment > 0,
  }));

  // Drop trailing months that have essentially no BNPL payment and tiny NCF change
  // (avoid lots of flat identical bars after the installment period ends)
  let cutoff = raw.length;
  for (let i = raw.length - 1; i >= 0; i--) {
    if (raw[i].is_bnpl || Math.abs(raw[i].ncf) > 500_000) { cutoff = i + 1; break; }
  }
  const data = raw.slice(0, Math.min(cutoff + 1, raw.length)); // keep 1 recovery month

  const maxAbs = Math.max(...data.map(d => Math.abs(d.ncf)), 1);

  return (
    <ResponsiveContainer width="100%" height={100}>
      <BarChart data={data} margin={{ top: 2, right: 4, left: -20, bottom: 0 }}>
        <XAxis dataKey="label" tick={{ fontSize: 9, fill: '#94a3b8' }} />
        <YAxis hide domain={[-maxAbs * 1.2, maxAbs * 1.2]} />
        <ReferenceLine y={0} stroke="#cbd5e1" strokeDasharray="3 3" />
        <Tooltip
          formatter={(v) => [`${(Number(v) / 1e6).toFixed(1)}M ₫`, 'Dòng tiền']}
          contentStyle={{ fontSize: 11, borderRadius: 6, border: '1px solid #E2E8F0' }}
        />
        <Bar dataKey="ncf" radius={[2, 2, 0, 0]}>
          {data.map((entry, i) => (
            <Cell
              key={i}
              fill={entry.ncf >= 0 ? '#3B82F6' : '#EF4444'}
              opacity={entry.is_bnpl ? 1 : 0.5}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

function PlanCard({
  opt, purchase_amount, maxAbsNcf, isBest, sim,
}: {
  opt: OptionScoreOut;
  purchase_amount: number;
  maxAbsNcf: number;
  isBest?: boolean;
  sim?: ScenarioSimulationOut | null;
}) {
  const name = getPlanName(opt.option_id);
  const totalCost = purchase_amount + opt.total_interest;
  const riskColor = opt.risk_score < 30 ? 'var(--color-success)' : opt.risk_score < 60 ? 'var(--color-warning)' : 'var(--color-danger)';
  const riskLabel = opt.risk_score < 30 ? 'Thấp' : opt.risk_score < 60 ? 'Trung bình' : 'Cao';
  const installMonths = getInstallMonths(opt.option_id);
  const monthlyRate = installMonths > 0 && opt.total_interest > 0
    ? (opt.total_interest / purchase_amount / installMonths * 100)
    : 0;

  return (
    <div className={`plan-card ${isBest ? 'plan-card--best' : ''}`}>
      {isBest && <div className="plan-badge-best">Khuyến nghị</div>}

      <div className="plan-card-header">
        <span className="plan-card-name">{name}</span>
        <span className="plan-card-risk" style={{ color: riskColor }}>
          Rủi ro: {riskLabel}
        </span>
      </div>

      <div className="plan-card-costs">
        <div className="plan-cost-item">
          <span>Tổng chi phí</span>
          <strong>{fmt(totalCost)}</strong>
        </div>
        {opt.monthly_payment > 0 && (
          <div className="plan-cost-item">
            <span>Trả hàng tháng</span>
            <strong>{fmt(opt.monthly_payment)}</strong>
          </div>
        )}
        {opt.total_interest > 0 && (
          <div className="plan-cost-item">
            <span>
              Lãi / phí
              {monthlyRate > 0 && (
                <span className="plan-cost-rate"> ({monthlyRate.toFixed(1)}%/tháng)</span>
              )}
            </span>
            <strong style={{ color: 'var(--color-warning)' }}>{fmt(opt.total_interest)}</strong>
          </div>
        )}
      </div>

      <div className="plan-card-ncf">
        <span className="plan-ncf-label">Dự báo dòng tiền</span>
        {sim ? (
          <CashFlowChart sim={sim} />
        ) : (
          <div className="ncf-bar-wrap">
            <div className="ncf-bar-track">
              <div className="ncf-bar-center" />
              {opt.ncf_new >= 0 ? (
                <div className="ncf-bar-fill ncf-pos"
                  style={{ width: `${Math.min(50, Math.abs(opt.ncf_new) / maxAbsNcf * 50)}%`, left: '50%' }} />
              ) : (
                <div className="ncf-bar-fill ncf-neg"
                  style={{ width: `${Math.min(50, Math.abs(opt.ncf_new) / maxAbsNcf * 50)}%`, right: '50%' }} />
              )}
            </div>
            <span className="ncf-bar-label"
              style={{ color: opt.ncf_new >= 0 ? 'var(--color-success)' : 'var(--color-danger)' }}>
              {opt.ncf_new >= 0 ? '+' : ''}{(opt.ncf_new / 1e6).toFixed(1)}M ₫/tháng
            </span>
          </div>
        )}
      </div>

      {opt.explanation && (
        <div className="plan-card-explain">
          <div className="plan-explain-badge">🤖 AI</div>
          <p className="plan-explain-text">{opt.explanation}</p>
        </div>
      )}

      {opt.flags.length > 0 && (
        <div className="plan-card-flags">
          {opt.flags.map(f => (
            <span key={f} className="plan-flag">{translateFlag(f)}</span>
          ))}
        </div>
      )}
    </div>
  );
}

export function ComparisonResults() {
  const location = useLocation();
  const state = location.state as LocationState | null;
  const navigate = useNavigate();
  const [showAll, setShowAll] = useState(false);
  const [simulations, setSimulations] = useState<Record<string, ScenarioSimulationOut>>({});

  useEffect(() => {
    if (!state?.profile_id || !state.candidate_plans) return;
    const { profile_id, cif, purchase_amount, candidate_plans } = state;
    const horizon = Math.max(...candidate_plans.map(p => (p.months ?? 1) + 3), 6);

    Promise.all(
      candidate_plans.map(plan =>
        simulatePurchase({
          profile_id,
          cif,
          purchase_amount,
          option_type: plan.type,
          term_months: plan.months,
          apr: plan.apr,
          horizon_months: horizon,
          use_forecast: true,
        }).catch(() => null)
      )
    ).then(results => {
      const map: Record<string, ScenarioSimulationOut> = {};
      results.forEach(sim => { if (sim) map[sim.option_id] = sim; });
      setSimulations(map);
    });
  }, []);

  if (!state) { navigate('/advisor'); return null; }

  const { result, item_name, purchase_amount } = state;
  const sorted = [...result.options].sort((a, b) => a.risk_score - b.risk_score);
  const best = result.options.find(o => o.option_id === result.best_option_id) ?? sorted[0];
  const others = sorted.filter(o => o.option_id !== best.option_id);
  const maxAbsNcf = Math.max(...result.options.map(o => Math.abs(o.ncf_new)), 1);

  return (
    <div className="results-page">
      <div className="page-header">
        <button className="back-btn" onClick={() => navigate('/advisor')}>←</button>
        <div>
          <h1>Kết quả phân tích</h1>
          <div className="results-subtitle">{item_name} · {fmt(purchase_amount)}</div>
        </div>
      </div>

      <div className="page-body">
        <PlanCard
          opt={best}
          purchase_amount={purchase_amount}
          maxAbsNcf={maxAbsNcf}
          isBest
          sim={simulations[best.option_id]}
        />

        <button className="toggle-plans-btn" onClick={() => setShowAll(v => !v)}>
          {showAll ? 'Thu gọn ↑' : `Xem tất cả ${others.length + 1} phương án ↓`}
        </button>

        {showAll && (
          <div className="all-plans-grid">
            {sorted.map(opt => (
              <PlanCard
                key={opt.option_id}
                opt={opt}
                purchase_amount={purchase_amount}
                maxAbsNcf={maxAbsNcf}
                isBest={opt.option_id === best.option_id}
                sim={simulations[opt.option_id]}
              />
            ))}
          </div>
        )}

        <button className="primary-btn" onClick={() => navigate('/advisor')}>
          Tư vấn lại
        </button>
      </div>
    </div>
  );
}
