import { useLocation, useNavigate } from 'react-router-dom';
import type { OptionScoreOut } from '../api/types';
import { RiskGauge } from '../components/ui/RiskGauge';
import './pages.css';
import './OptionDetail.css';

const fmt = (n: number) => n >= 1_000_000
  ? `${(n / 1_000_000).toFixed(2)}M ₫`
  : `${n.toLocaleString('vi-VN')} ₫`;

const OPTION_NAMES: Record<string, string> = {
  'pay_in_full': 'Trả thẳng',
  'installment_6': 'Trả góp 6 tháng',
  'installment_12': 'Trả góp 12 tháng',
  'installment_4': 'Trả góp 4 tháng',
  'bnpl_4': 'BNPL 4 kỳ',
  'cc_12': 'Thẻ tín dụng',
};

interface LocationState {
  option: OptionScoreOut;
  item_name: string;
  purchase_amount: number;
}

export function OptionDetail() {
  const location = useLocation();
  const state = location.state as LocationState | null;
  const navigate = useNavigate();

  if (!state) { navigate('/advisor'); return null; }
  const { option: opt, purchase_amount } = state;
  const name = OPTION_NAMES[opt.option_id] ?? opt.option_id.replace(/_/g, ' ');

  return (
    <div className="detail-page">
      <div className="page-header">
        <button className="back-btn" onClick={() => navigate(-1)}>←</button>
        <h1>Chi tiết phương án</h1>
      </div>

      <div className="page-body">
        <div className="detail-two-col">
          {/* Left: gauge + cost summary */}
          <div className="section-card" style={{ textAlign: 'center' }}>
            <h2 style={{ marginBottom: 12, fontSize: 'var(--text-lg)', fontWeight: 700 }}>{name}</h2>
            <RiskGauge score={opt.risk_score} size={130} />
            <div className="detail-table" style={{ marginTop: 16, textAlign: 'left' }}>
              <div className="detail-row">
                <span>Tổng chi phí</span>
                <strong>{fmt(purchase_amount + opt.total_interest)}</strong>
              </div>
              {opt.monthly_payment > 0 && (
                <div className="detail-row">
                  <span>Thanh toán/tháng</span>
                  <strong>{fmt(opt.monthly_payment)}</strong>
                </div>
              )}
              <div className="detail-row">
                <span>Lãi vay</span>
                <strong>{fmt(opt.total_interest)}</strong>
              </div>
            </div>
          </div>

          {/* Right: impacts + AI */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div className="section-card">
              <h3 className="section-title">Tác động tài chính</h3>
              <ImpactRow label="NCF" after={opt.ncf_new} afterLabel={fmt(opt.ncf_new)} progress={Math.max(0, opt.ncf_new) / 30_000_000} />
              <ImpactRow label="DTI" after={opt.dti_new} afterLabel={`${opt.dti_new.toFixed(1)}%`} progress={opt.dti_new / 60} invert />
              <ImpactRow label="Quỹ khẩn cấp" after={opt.efr_after} afterLabel={`${opt.efr_after.toFixed(1)} tháng`} progress={opt.efr_after / 12} />
            </div>

            <div className="ai-explanation">
              <div className="ai-badge">Phân tích AI</div>
              <p className="ai-text">{opt.explanation || opt.key_factors?.join('. ')}</p>
            </div>

            {opt.flags.length > 0 && (
              <div className="flags-card">
                {opt.flags.map(f => <div key={f} className="flag-item">{f}</div>)}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function ImpactRow({ label, after, afterLabel, progress, invert }: {
  label: string; after: number; afterLabel: string; progress: number; invert?: boolean;
}) {
  const clamped = Math.min(1, Math.max(0, progress));
  const isGood = invert ? after <= 35 : after >= 0;
  const color = isGood ? 'var(--color-success)' : 'var(--color-danger)';
  return (
    <div className="impact-row">
      <div className="impact-header">
        <span className="impact-label">{label}</span>
        <span className="impact-value" style={{ color }}>{afterLabel}</span>
      </div>
      <div className="impact-bar">
        <div className="impact-fill" style={{ width: `${clamped * 100}%`, background: color }} />
      </div>
    </div>
  );
}
