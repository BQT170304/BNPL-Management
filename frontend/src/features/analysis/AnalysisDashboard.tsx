// frontend/src/features/analysis/AnalysisDashboard.tsx
import { useEffect } from "react";
import { getAnalysis } from "../../api/endpoints";
import { Badge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Metric } from "../../components/ui/Metric";
import { Spinner } from "../../components/ui/Spinner";
import { useAsync } from "../../hooks/useAsync";
import { dtiBandClass, riskClass } from "../../lib/bands";
import { formatVnd } from "../../lib/money";

export function AnalysisDashboard({ profileId }: { profileId: string }) {
  const { run, data, loading, error } = useAsync(getAnalysis);

  useEffect(() => {
    run(profileId).catch(() => undefined);
  }, [run, profileId]);

  if (loading) return <Spinner />;
  if (error) return <ErrorBanner message={error} />;
  if (!data) return null;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
        <Metric label="Dòng tiền ròng (NCF)" value={formatVnd(data.ncf)} />
        <Metric
          label="DTI"
          value={`${data.dti.toFixed(1)}%`}
          hint={<Badge className={dtiBandClass(data.dti_band)}>{data.dti_band}</Badge>}
        />
        <Metric label="Tỷ lệ tiết kiệm" value={`${data.saving_rate.toFixed(1)}%`}
          hint="Khuyến nghị ≥ 20%" />
        <Metric label="Quỹ khẩn cấp (EFR)" value={`${data.efr.toFixed(2)} tháng`}
          hint="An toàn ≥ 3 tháng" />
        <Metric label="Rủi ro danh mục (PGRS)" value={data.pgrs.toFixed(0)}
          hint={<Badge className={riskClass(data.pgrs)}>{data.pgrs.toFixed(0)}/100</Badge>} />
      </div>

      {data.flags.length > 0 && (
        <ErrorBanner message={`Cảnh báo: ${data.flags.join(", ")}`} />
      )}

      <Card title="Mục tiêu">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-500">
              <th className="py-1">Mục tiêu</th>
              <th>Còn thiếu</th>
              <th>Phân bổ/tháng</th>
              <th>Còn lại (tháng)</th>
              <th>Rủi ro</th>
            </tr>
          </thead>
          <tbody>
            {data.goals.map((g) => (
              <tr key={g.goal_id} className="border-t border-slate-100">
                <td className="py-2">{g.name}</td>
                <td>{formatVnd(g.gap)}</td>
                <td>{formatVnd(g.monthly_allocated)}</td>
                <td>{g.months_remaining}</td>
                <td><Badge className={riskClass(g.grs)}>{g.grs.toFixed(0)}</Badge></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
