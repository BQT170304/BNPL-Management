import { useEffect, useState } from 'react';
import { getAnalysis } from '../api/endpoints';
import type { MetricsOut, GoalMetricOut } from '../api/types';
import { HealthGauge } from '../components/ui/HealthGauge';
import './FinancialHealth.css';

const fmtM = (n: number) => n >= 1_000_000 ? `${(n / 1_000_000).toFixed(1)}M ₫` : `${n.toLocaleString('vi-VN')} ₫`;

interface Props { profileId: string; }

export function FinancialHealth({ profileId }: Props) {
  const [metrics, setMetrics] = useState<MetricsOut | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAnalysis(profileId).then(setMetrics).finally(() => setLoading(false));
  }, [profileId]);

  if (loading) return <div className="page-loading"><div className="spinner" /></div>;
  if (!metrics) return <div style={{ padding: 20 }}>Không tải được dữ liệu</div>;

  const metricDefs = [
    {
      key: 'ncf',
      label: 'Dòng tiền ròng',
      value: fmtM(metrics.ncf),
      progress: Math.max(0, Math.min(1, metrics.ncf / 10_000_000)),
    },
    {
      key: 'dti',
      label: 'Tỷ lệ nợ / Thu nhập',
      value: `${metrics.dti.toFixed(1)}%`,
      progress: Math.max(0, 1 - metrics.dti / 60),
    },
    {
      key: 'saving_rate',
      label: 'Tỷ lệ tiết kiệm',
      value: `${metrics.saving_rate.toFixed(1)}%`,
      progress: Math.max(0, Math.min(1, metrics.saving_rate / 40)),
    },
    {
      key: 'efr',
      label: 'Quỹ khẩn cấp',
      value: `${metrics.efr.toFixed(1)} tháng`,
      progress: Math.max(0, Math.min(1, metrics.efr / 12)),
    },
  ];

  return (
    <div className="health-page">
      <div className="health-hero">
        <h1>Sức khỏe tài chính</h1>
        <HealthGauge score={metrics.overall_health_score} size={130} />
      </div>

      <div className="page-body">
        {metricDefs.map(m => {
          const st = metrics.metric_statuses?.[m.key];
          const color = st === 'healthy' ? 'var(--color-success)' : st === 'warning' ? 'var(--color-warning)' : 'var(--color-danger)';
          const badge = st === 'healthy' ? 'Tốt' : st === 'warning' ? 'Cần chú ý' : 'Rủi ro';
          return (
            <div key={m.key} className="hm-card">
              <div className="hm-row">
                <span className="hm-label">{m.label}</span>
                <div className="hm-right">
                  <span className="hm-value">{m.value}</span>
                  <span className="hm-badge" style={{ background: color + '22', color }}>{badge}</span>
                </div>
              </div>
              <div className="hm-bar">
                <div className="hm-bar-fill" style={{ width: `${m.progress * 100}%`, background: color }} />
              </div>
            </div>
          );
        })}

        {metrics.goals.length > 0 && (
          <div className="hm-goals-card">
            <span className="hm-goals-title">Mục tiêu tài chính</span>
            {metrics.goals.map((g: GoalMetricOut) => {
              const statusColor = g.grs > 50 ? 'var(--color-danger)' : g.grs > 20 ? 'var(--color-warning)' : 'var(--color-success)';
              const statusLabel = g.grs > 50 ? 'Trễ tiến độ' : g.grs > 20 ? 'Cần tăng tốc' : 'Đúng lộ trình';
              return (
                <div key={g.goal_id} className="goal-detail">
                  <div className="goal-detail-header">
                    <span className="goal-detail-name">{g.name}</span>
                    <span style={{ fontSize: 11, color: statusColor, fontWeight: 600 }}>{statusLabel}</span>
                  </div>
                  <div className="hm-bar" style={{ marginTop: 6 }}>
                    <div className="hm-bar-fill" style={{
                      width: `${Math.min(100, (1 - g.grs / 100) * 100)}%`,
                      background: statusColor,
                    }} />
                  </div>
                  <div className="goal-detail-meta">
                    <span>{fmtM(g.monthly_allocated)}/tháng</span>
                    <span>{g.delay > 0 ? `Trễ ${g.delay.toFixed(0)} tháng` : 'Đúng hạn'}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

