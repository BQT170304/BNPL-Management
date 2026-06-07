import { useEffect, useState } from 'react';
import { getForecast } from '../api/endpoints';
import type { ForecastOut, HistoryPointOut, ForecastPointOut } from '../api/types';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import './pages.css';
import './CashFlowForecast.css';

interface Props { cif: string; }

interface ChartPoint {
  ds: string;
  y?: number;
  type: string;
}

export function CashFlowForecast({ cif }: Props) {
  const [data, setData] = useState<ForecastOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!cif) { setLoading(false); return; }
    getForecast(cif)
      .then(setData)
      .catch(() => setError('Chua co du lieu giao dich'))
      .finally(() => setLoading(false));
  }, [cif]);

  if (loading) return <div className="page-loading"><div className="spinner"/></div>;

  const chartData: ChartPoint[] = data ? [
    ...data.history.map((h: HistoryPointOut) => ({ ds: h.ds.slice(5, 10), y: h.y, type: 'hist' })),
    ...data.forecast.slice(0, 30).map((f: ForecastPointOut) => ({ ds: f.ds.slice(5, 10), y: f.yhat, type: 'fore' })),
  ] : [];

  return (
    <div className="forecast-page">
      <div className="forecast-hero">
        <h1>📈 Du bao dong tien</h1>
        <p>Xu huong 30/90 ngay toi</p>
      </div>

      <div className="page-body">
        {error ? (
          <div className="section-card" style={{ textAlign: 'center', padding: 40, color: 'var(--color-text-muted)' }}>
            <div style={{ fontSize: 40 }}>📊</div>
            <p style={{ marginTop: 12 }}>{error}</p>
            <p style={{ fontSize: 12, marginTop: 8 }}>Upload giao dich de xem du bao</p>
          </div>
        ) : data ? (
          <>
            <div className="forecast-summary">
              <SummaryCard label="30 ngay" value={`${(data.next_30_net/1_000_000).toFixed(1)}M`} positive={data.next_30_net >= 0} />
              <SummaryCard label="90 ngay" value={`${(data.next_90_net/1_000_000).toFixed(1)}M`} positive={data.next_90_net >= 0} />
            </div>

            <div className="section-card">
              <h3 className="section-title">Bieu do dong tien</h3>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                  <XAxis dataKey="ds" tick={{ fontSize: 9 }} interval={6} />
                  <YAxis tick={{ fontSize: 9 }} tickFormatter={(v: number) => `${(v/1e6).toFixed(0)}M`} />
                  <Tooltip formatter={(v) => [`${(Number(v)/1e6).toFixed(2)}M D`, 'Dong tien']} />
                  <ReferenceLine y={0} stroke="#EF4444" strokeDasharray="4 4" />
                  <Line type="monotone" dataKey="y" stroke="#1D4ED8" strokeWidth={2} dot={false} connectNulls />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="section-card">
              <h3 className="section-title">Nhan dinh</h3>
              <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
                Dong tien du kien {data.next_30_net >= 0 ? 'duong' : 'am'} trong 30 ngay toi voi gia tri {(data.next_30_net/1_000_000).toFixed(1)}M.
                {data.next_30_net >= 0 ? ' Tinh trang tai chinh on dinh.' : ' Can chu y kiem soat chi tieu.'}
              </p>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}

function SummaryCard({ label, value, positive }: { label: string; value: string; positive: boolean }) {
  return (
    <div className="summary-card">
      <span className="summary-period">{label}</span>
      <span className="summary-value" style={{ color: positive ? 'var(--color-success)' : 'var(--color-danger)' }}>
        {positive ? '+' : ''}{value}
      </span>
      <span className="summary-trend">{positive ? '↗️ Tang' : '↘️ Giam'}</span>
    </div>
  );
}
