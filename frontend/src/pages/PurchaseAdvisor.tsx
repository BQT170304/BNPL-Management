import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { evaluatePurchase } from '../api/endpoints';
import { parseVnd, formatVnd } from '../lib/money';
import './pages.css';
import './PurchaseAdvisor.css';

const CATEGORIES = ['Công nghệ', 'Thời trang', 'Gia dụng', 'Du lịch', 'Giáo dục', 'Khác'];

// Vietnamese market rates (Kredivo benchmark: 0% ≤3 months, 2%–2.1%/tháng after)
const ALL_PLANS = [
  { label: 'Trả thẳng',    type: 'PAY_IN_FULL' as const, months: null as number | null, apr: 0 },
  { label: 'BNPL 1 tháng', type: 'INSTALLMENT' as const, months: 1,  apr: 0 },
  { label: 'BNPL 3 tháng', type: 'INSTALLMENT' as const, months: 3,  apr: 0 },
  { label: 'BNPL 6 tháng', type: 'INSTALLMENT' as const, months: 6,  apr: 24 },
  { label: 'BNPL 12 tháng',type: 'INSTALLMENT' as const, months: 12, apr: 25.2 },
];

interface Props { profileId: string; cif: string; }

export function PurchaseAdvisor({ profileId, cif }: Props) {
  const navigate = useNavigate();
  const [itemName, setItemName] = useState('');
  const [amount, setAmount] = useState(0);
  const [category, setCategory] = useState(CATEGORIES[0]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    if (!itemName.trim() || amount <= 0) {
      setError('Vui lòng nhập đầy đủ thông tin');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const result = await evaluatePurchase({
        profile_id: profileId,
        item_name: itemName,
        purchase_amount: amount,
        candidate_plans: ALL_PLANS.map(p => ({ type: p.type, months: p.months, apr: p.apr })),
      });
      navigate('/results', {
        state: {
          result,
          item_name: itemName,
          purchase_amount: amount,
          profile_id: profileId,
          cif,
          candidate_plans: ALL_PLANS,
        },
      });
    } catch (e: unknown) {
      const err = e as { message?: string };
      setError(err.message || 'Có lỗi xảy ra');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="advisor-page">
      <div className="page-header">
        <button className="back-btn" onClick={() => navigate('/')}>←</button>
        <h1>Tư vấn thanh toán</h1>
      </div>

      <div className="page-body">
        <div className="section-card">
          <div className="section-title">Thông tin sản phẩm</div>

          <div className="form-field">
            <label>Tên sản phẩm</label>
            <input
              className="form-input"
              placeholder="VD: Laptop MacBook Air"
              value={itemName}
              onChange={e => setItemName(e.target.value)}
            />
          </div>

          <div className="form-field">
            <label>Số tiền (₫)</label>
            <input
              type="text"
              inputMode="numeric"
              className="form-input"
              placeholder="VD: 25.000.000"
              value={amount === 0 ? '' : formatVnd(amount).replace(' ₫', '')}
              onChange={e => setAmount(parseVnd(e.target.value))}
            />
          </div>

          <div className="form-field" style={{ marginBottom: 0 }}>
            <label>Danh mục</label>
            <select className="form-select" value={category} onChange={e => setCategory(e.target.value)}>
              {CATEGORIES.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
        </div>

        {error && <div className="error-msg">{error}</div>}

        <button className="primary-btn" onClick={handleSubmit} disabled={loading}>
          {loading ? 'Đang phân tích 5 kịch bản...' : 'Phân tích ngay'}
        </button>
      </div>
    </div>
  );
}
