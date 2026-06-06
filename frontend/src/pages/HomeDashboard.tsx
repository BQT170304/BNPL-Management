import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAnalysis, getForecast, getHomeAdvice } from '../api/endpoints';
import type { MetricsOut, GoalMetricOut, ForecastOut, AdviceOut } from '../api/types';
import { HealthGauge } from '../components/ui/HealthGauge';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, Cell } from 'recharts';
import './HomeDashboard.css';

const fmtM = (n: number) => {
  const abs = Math.abs(n);
  if (abs >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return n.toLocaleString('vi-VN');
};

const fmtFull = (n: number) => n >= 1_000_000
  ? `${(n / 1_000_000).toFixed(1)}M ₫`
  : `${n.toLocaleString('vi-VN')} ₫`;

interface Props { profileId: string; cif: string; }

export function HomeDashboard({ profileId, cif }: Props) {
  const [metrics, setMetrics] = useState<MetricsOut | null>(null);
  const [forecast, setForecast] = useState<ForecastOut | null>(null);
  const [advice, setAdvice] = useState<AdviceOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [adviceLoading, setAdviceLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    // Load metrics + forecast first so page renders immediately
    Promise.all([
      getAnalysis(profileId),
      getForecast(cif).catch(() => null),
    ]).then(([m, f]) => {
      setMetrics(m);
      setForecast(f);
    }).finally(() => setLoading(false));

    // AI advice loads independently — card shows its own skeleton
    getHomeAdvice(profileId)
      .then(a => setAdvice(a))
      .catch(() => setAdvice(null))
      .finally(() => setAdviceLoading(false));
  }, [profileId, cif]);

  if (loading) return <div className="page-loading"><div className="spinner" /></div>;
  if (!metrics) return <div style={{ padding: 20 }}>Không tải được dữ liệu</div>;

  const chartData = (() => {
    if (!forecast) return [];
    const agg = (entries: Array<{ ds: string; value: number }>) => {
      const map = new Map<string, number>();
      entries.forEach(({ ds, value }) => {
        const month = ds.slice(0, 7); // YYYY-MM
        map.set(month, (map.get(month) ?? 0) + value);
      });
      return Array.from(map.entries())
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([month, y]) => ({ ds: month.slice(5) + '/' + month.slice(0, 4), y, rawMonth: month }));
    };
    const allHist = agg(forecast.history.map(h => ({ ds: h.ds, value: h.y })));
    const allFcast = agg(forecast.forecast.map(f => ({ ds: f.ds, value: f.yhat })));

    // Show last 6 history months + up to 4 forecast months with non-trivial values
    const histMonths = allHist.slice(-6);
    const lastHistRaw = histMonths[histMonths.length - 1]?.rawMonth;
    const fcastMonths: Array<{ ds: string; y: number; rawMonth: string; forecast: boolean }> = allFcast
      .filter(f => f.rawMonth > (lastHistRaw ?? ''))
      .slice(0, 4)
      .map(f => ({ ...f, forecast: true as const }));

    return [
      ...histMonths.map(h => ({ ...h, forecast: false as const })),
      ...fcastMonths,
    ];
  })();

  const metricDefs = [
    { key: 'ncf',         label: 'Dòng tiền ròng',     value: `${fmtM(metrics.ncf)} ₫`,          progress: Math.max(0, Math.min(1, metrics.ncf / 10_000_000)) },
    { key: 'dti',         label: 'Tỷ lệ nợ/thu nhập',  value: `${metrics.dti.toFixed(1)}%`,       progress: Math.max(0, 1 - metrics.dti / 60) },
    { key: 'saving_rate', label: 'Tỷ lệ tiết kiệm',    value: `${metrics.saving_rate.toFixed(1)}%`, progress: Math.max(0, Math.min(1, metrics.saving_rate / 40)) },
    { key: 'efr',         label: 'Quỹ khẩn cấp',       value: `${metrics.efr.toFixed(1)} tháng`, progress: Math.max(0, Math.min(1, metrics.efr / 12)) },
  ];

  return (
    <div className="home-page">
      <div className="hero-header">
        <div className="hero-text">
          <span className="hero-greeting">Chào Minh</span>
          <span className="hero-subtitle">Tổng quan tài chính của bạn</span>
        </div>
        <HealthGauge score={metrics.overall_health_score} size={110} />
      </div>

      <div className="page-body">
        {/* AI advice card — shows skeleton while LLM is processing */}
        {(adviceLoading || advice) && (
          <div className="home-ai-card">
            <div className="home-ai-badge">🤖 AI</div>
            {adviceLoading ? (
              <div className="home-ai-skeleton">
                <div className="home-ai-skeleton-line" />
                <div className="home-ai-skeleton-line home-ai-skeleton-line--short" />
              </div>
            ) : (
              <p className="home-ai-text">{advice?.advice}</p>
            )}
          </div>
        )}

        {/* 4 metric cards with status */}
        <div className="metrics-grid">
          {metricDefs.map(m => {
            const st = metrics.metric_statuses?.[m.key];
            return <MetricCard key={m.key} label={m.label} value={m.value} status={st} progress={m.progress} />;
          })}
        </div>

        <div className="home-two-col">
          {/* Left: advisor CTA + goals */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div className="advisory-cta" onClick={() => navigate('/advisor')}>
              <div className="cta-text">
                <span className="cta-title">Tư vấn thanh toán</span>
                <span className="cta-desc">Phân tích phương án mua sắm tối ưu</span>
              </div>
              <button className="cta-arrow">→</button>
            </div>

            {metrics.goals.length > 0 && (
              <div className="home-section-card">
                <span className="home-section-title">Mục tiêu tài chính</span>
                {metrics.goals.map((g: GoalMetricOut) => {
                  const statusColor = g.grs > 50 ? 'var(--color-danger)' : g.grs > 20 ? 'var(--color-warning)' : 'var(--color-success)';
                  const statusLabel = g.grs > 50 ? 'Trễ tiến độ' : g.grs > 20 ? 'Cần tăng tốc' : 'Đúng lộ trình';
                  return (
                    <div key={g.goal_id} className="goal-detail">
                      <div className="goal-detail-header">
                        <span className="goal-detail-name">{g.name}</span>
                        <span style={{ fontSize: 11, color: statusColor, fontWeight: 600 }}>{statusLabel}</span>
                      </div>
                      <div className="goal-bar">
                        <div className="goal-bar-fill" style={{
                          width: `${Math.min(100, (1 - g.grs / 100) * 100)}%`,
                          background: statusColor,
                        }} />
                      </div>
                      <div className="goal-detail-meta">
                        <span>{fmtFull(g.monthly_allocated)}/tháng</span>
                        <span>{g.delay > 0 ? `Trễ ${g.delay.toFixed(0)} tháng` : 'Đúng hạn'}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Right: forecast chart */}
          {forecast && (
            <div className="home-section-card">
              <div className="forecast-header">
                <span className="home-section-title">Dự báo dòng tiền</span>
                <div className="forecast-pills">
                  <span className="pill" style={{ color: forecast.next_30_net >= 0 ? 'var(--color-success)' : 'var(--color-danger)' }}>
                    30 ngày: {forecast.next_30_net >= 0 ? '+' : ''}{fmtM(forecast.next_30_net)}
                  </span>
                  <span className="pill" style={{ color: forecast.next_90_net >= 0 ? 'var(--color-success)' : 'var(--color-danger)' }}>
                    90 ngày: {forecast.next_90_net >= 0 ? '+' : ''}{fmtM(forecast.next_90_net)}
                  </span>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={chartData} margin={{ top: 4, right: 4, left: -10, bottom: 0 }}>
                  <XAxis dataKey="ds" tick={{ fontSize: 10, fill: '#74777f' }} />
                  <YAxis tick={{ fontSize: 10, fill: '#74777f' }} tickFormatter={v => `${(v / 1e6).toFixed(0)}M`} />
                  <Tooltip
                    formatter={(v) => [`${(Number(v) / 1e6).toFixed(1)}M ₫`, 'Dòng tiền']}
                    contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #E2E8F0' }}
                  />
                  <ReferenceLine y={0} stroke="#94a3b8" />
                  <Bar dataKey="y" radius={[4, 4, 0, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell
                        key={index}
                        fill={entry.forecast ? (entry.y >= 0 ? '#93C5FD' : '#FCA5A5') : (entry.y >= 0 ? '#3B82F6' : '#EF4444')}
                        opacity={entry.forecast ? 0.7 : 1}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function MetricCard({ label, value, status, progress }: {
  label: string; value: string; status?: string; progress: number;
}) {
  const color = status === 'healthy' ? 'var(--color-success)' : status === 'warning' ? 'var(--color-warning)' : 'var(--color-danger)';
  const badge = status === 'healthy' ? 'Tốt' : status === 'warning' ? 'Cần chú ý' : 'Rủi ro';
  return (
    <div className="metric-card">
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      <span className="metric-badge" style={{ background: color + '22', color }}>{badge}</span>
      <div className="metric-bar">
        <div className="metric-bar-fill" style={{ width: `${progress * 100}%`, background: color }} />
      </div>
    </div>
  );
}
