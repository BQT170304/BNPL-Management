import { useEffect, useState } from "react";
import { getForecast, getForecastChart } from "../../api/endpoints";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Metric } from "../../components/ui/Metric";
import { Spinner } from "../../components/ui/Spinner";
import { useAsync } from "../../hooks/useAsync";
import { formatVnd } from "../../lib/money";

const CIF = "10001234";

export function CashflowForecast() {
  const summary = useAsync(getForecast);
  const chart = useAsync(getForecastChart);
  const [objectUrl, setObjectUrl] = useState<string | null>(null);

  useEffect(() => {
    let url: string | null = null;
    summary.run(CIF).catch(() => undefined);
    chart
      .run(CIF)
      .then((blob) => {
        url = URL.createObjectURL(blob);
        setObjectUrl(url);
      })
      .catch(() => undefined);
    return () => {
      if (url) URL.revokeObjectURL(url);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const error = summary.error ?? chart.error;

  return (
    <div className="space-y-4">
      {error && <ErrorBanner message={error} />}

      {summary.data && (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <Metric
            label="Dòng tiền dự báo 30 ngày"
            value={formatVnd(Math.round(summary.data.next_30_net))}
          />
          <Metric
            label="Dòng tiền dự báo 90 ngày"
            value={formatVnd(Math.round(summary.data.next_90_net))}
          />
        </div>
      )}

      <Card title="Biểu đồ dự báo dòng tiền (CIF 10001234)">
        {objectUrl ? (
          <img alt="Biểu đồ dự báo dòng tiền" src={objectUrl} />
        ) : (
          <Spinner />
        )}
      </Card>
    </div>
  );
}
