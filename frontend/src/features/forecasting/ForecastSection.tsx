import { useEffect } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getAnalysis, getForecast } from "../../api/endpoints";
import type { ForecastOut } from "../../api/types";
import { useAsync } from "../../hooks/useAsync";
import { formatVnd } from "../../lib/money";

function shortVnd(v: number): string {
  if (Math.abs(v) >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}tr`;
  if (Math.abs(v) >= 1_000) return `${(v / 1_000).toFixed(0)}K`;
  return String(v);
}

function sum(arr: number[]): number {
  return arr.reduce((a, b) => a + b, 0);
}

type ChartPoint = {
  date: string;
  actual: number | null;
  yhat: number | null;
  bandBase: number | null;
  bandWidth: number | null;
};

// Return the Monday of the week containing ds (YYYY-MM-DD)
function weekStart(ds: string): string {
  const d = new Date(ds + "T00:00:00");
  const day = d.getDay(); // 0=Sun
  const diff = day === 0 ? -6 : 1 - day;
  d.setDate(d.getDate() + diff);
  return d.toISOString().slice(0, 10);
}

function prepWeekly(fc: ForecastOut): { data: ChartPoint[]; splitDate: string | null } {
  // ── history → weekly sums ──────────────────────────────────────────────────
  const histMap = new Map<string, number[]>();
  fc.history.forEach((h) => {
    const key = weekStart(h.ds);
    histMap.set(key, [...(histMap.get(key) ?? []), h.y]);
  });

  const histWeekly = [...histMap.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .slice(-52) // last 52 weeks
    .map(([date, vals]) => ({
      date,
      actual: sum(vals),
      yhat: null as number | null,
      bandBase: null as number | null,
      bandWidth: null as number | null,
    }));

  const lastHistWeek = histWeekly.length > 0 ? histWeekly[histWeekly.length - 1].date : null;

  // ── forecast → weekly sums, skip weeks already in history ─────────────────
  const foreMap = new Map<string, { yhats: number[]; lowers: number[]; uppers: number[] }>();
  fc.forecast.forEach((f) => {
    const key = weekStart(f.ds);
    if (lastHistWeek && key <= lastHistWeek) return; // skip overlap
    const entry = foreMap.get(key) ?? { yhats: [], lowers: [], uppers: [] };
    entry.yhats.push(f.yhat);
    entry.lowers.push(f.lower);
    entry.uppers.push(f.upper);
    foreMap.set(key, entry);
  });

  const foreWeekly: ChartPoint[] = [...foreMap.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, { yhats, lowers, uppers }]) => {
      const lower = sum(lowers);
      const upper = sum(uppers);
      return {
        date,
        actual: null,
        yhat: sum(yhats),
        bandBase: lower,
        bandWidth: Math.max(0, upper - lower),
      };
    });

  // The gap between histWeekly and foreWeekly is natural: actual=null in fore,
  // yhat=null in hist → connectNulls={false} leaves a blank on each series.
  return { data: [...histWeekly, ...foreWeekly], splitDate: lastHistWeek };
}

function TipContent({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: { name: string; value: number; color: string }[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  const visible = payload.filter(
    (p) => p.value != null && !["Dải dự báo (nền)", "Dải dự báo"].includes(p.name),
  );
  if (!visible.length) return null;
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs shadow-md">
      <p className="mb-1.5 font-semibold text-slate-600">{label}</p>
      {visible.map((p) => (
        <p key={p.name} className="flex justify-between gap-4" style={{ color: p.color }}>
          <span>{p.name}</span>
          <span className="font-medium">{formatVnd(Math.round(p.value))}</span>
        </p>
      ))}
    </div>
  );
}

export function ForecastSection({ cif, profileId }: { cif: string; profileId: string }) {
  const fcAsync = useAsync(getForecast);
  const analysisAsync = useAsync(getAnalysis);

  useEffect(() => {
    fcAsync.run(cif).catch(() => undefined);
    analysisAsync.run(profileId).catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cif, profileId]);

  if (fcAsync.loading) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-3 h-4 w-52 animate-pulse rounded bg-slate-200" />
        <div className="h-56 animate-pulse rounded-lg bg-slate-100" />
      </div>
    );
  }

  const fc = fcAsync.data;
  if (!fc || fc.history.length === 0) return null;

  const { data, splitDate } = prepWeekly(fc);
  // Weekly equivalent of planned monthly NCF (4.33 weeks/month)
  const weeklyTarget = analysisAsync.data ? analysisAsync.data.ncf / 4.33 : null;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-3 flex items-start justify-between">
        <div>
          <p className="text-sm font-semibold text-slate-700">Xu hướng dòng tiền giao dịch</p>
          <p className="mt-0.5 text-xs text-slate-400">
            Lịch sử 52 tuần · dự báo {fc.forecast.length > 0 ? "12 tuần tới" : ""}
            {weeklyTarget != null && (
              <span className="ml-2 text-indigo-400">
                · kế hoạch {formatVnd(Math.round(weeklyTarget))}/tuần
              </span>
            )}
          </p>
        </div>
        <div className="flex gap-5 text-right">
          <div>
            <p className="text-[11px] text-slate-400">30 ngày tới</p>
            <p className={`text-sm font-semibold ${fc.next_30_net < 0 ? "text-red-600" : "text-emerald-600"}`}>
              {formatVnd(Math.round(fc.next_30_net))}
            </p>
          </div>
          <div>
            <p className="text-[11px] text-slate-400">90 ngày tới</p>
            <p className={`text-sm font-semibold ${fc.next_90_net < 0 ? "text-red-600" : "text-emerald-600"}`}>
              {formatVnd(Math.round(fc.next_90_net))}
            </p>
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 4 }}>
          <defs>
            <linearGradient id="foreGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#818cf8" stopOpacity={0.25} />
              <stop offset="100%" stopColor="#818cf8" stopOpacity={0.03} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 9 }}
            tickLine={false}
            axisLine={false}
            interval={Math.floor(data.length / 8)}
          />
          <YAxis
            tickFormatter={shortVnd}
            tick={{ fontSize: 10 }}
            width={44}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<TipContent />} />
          <Legend iconSize={10} wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />

          {/* Zero line */}
          <ReferenceLine y={0} stroke="#94a3b8" strokeDasharray="4 3" />

          {/* Planned NCF target */}
          {weeklyTarget != null && (
            <ReferenceLine
              y={weeklyTarget}
              stroke="#4f46e5"
              strokeDasharray="6 3"
              strokeOpacity={0.5}
              label={{
                value: "Kế hoạch",
                fontSize: 9,
                fill: "#6366f1",
                position: "insideTopRight",
              }}
            />
          )}

          {/* History / forecast boundary */}
          {splitDate && (
            <ReferenceLine
              x={splitDate}
              stroke="#c7d2fe"
              strokeDasharray="4 3"
              label={{
                value: "Hiện tại",
                fontSize: 9,
                fill: "#94a3b8",
                position: "insideTopRight",
              }}
            />
          )}

          {/* Confidence band */}
          <Area
            dataKey="bandBase"
            stackId="band"
            fill="transparent"
            stroke="none"
            name="Dải dự báo (nền)"
            dot={false}
            legendType="none"
          />
          <Area
            dataKey="bandWidth"
            stackId="band"
            fill="url(#foreGrad)"
            stroke="none"
            name="Khoảng tin cậy"
            dot={false}
            legendType="square"
          />

          {/* Actual history */}
          <Line
            dataKey="actual"
            stroke="#4f46e5"
            strokeWidth={2}
            dot={false}
            name="Thực tế"
            connectNulls={false}
          />

          {/* Forecast */}
          <Line
            dataKey="yhat"
            stroke="#818cf8"
            strokeWidth={2}
            strokeDasharray="5 3"
            dot={false}
            name="Dự báo"
            connectNulls={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
