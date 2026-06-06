import {
  Area,
  Bar,
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
import type { CashFlowMonthOut } from "../../api/types";
import { formatVnd } from "../../lib/money";

function shortVnd(v: number): string {
  if (Math.abs(v) >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}tr`;
  if (Math.abs(v) >= 1_000) return `${(v / 1_000).toFixed(0)}K`;
  return String(v);
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
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs shadow-md">
      <p className="mb-1.5 font-semibold text-slate-600">{label}</p>
      {payload.map((p) => (
        <p key={p.name} className="flex justify-between gap-4" style={{ color: p.color }}>
          <span>{p.name}</span>
          <span className="font-medium">{formatVnd(Math.round(p.value))}</span>
        </p>
      ))}
    </div>
  );
}

export function CashflowChart({ months }: { months: CashFlowMonthOut[] }) {
  const data = months.map((m) => ({
    name: m.year_month.slice(2),
    "Trả BNPL": m.bnpl_payment,
    "Dòng tiền ròng": m.net_cashflow,
    "Tích luỹ": m.cumulative_balance,
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart data={data} margin={{ top: 8, right: 56, bottom: 0, left: 4 }}>
        <defs>
          <linearGradient id="balGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
            <stop offset="90%" stopColor="#10b981" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
        <XAxis dataKey="name" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
        <YAxis
          yAxisId="L"
          tickFormatter={shortVnd}
          tick={{ fontSize: 10 }}
          width={44}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          yAxisId="R"
          orientation="right"
          tickFormatter={shortVnd}
          tick={{ fontSize: 10 }}
          width={50}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<TipContent />} />
        <Legend iconSize={10} wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />
        <ReferenceLine yAxisId="L" y={0} stroke="#94a3b8" strokeDasharray="4 4" />
        <Bar
          yAxisId="L"
          dataKey="Trả BNPL"
          fill="#f59e0b"
          opacity={0.8}
          radius={[2, 2, 0, 0]}
          maxBarSize={18}
        />
        <Line
          yAxisId="L"
          type="monotone"
          dataKey="Dòng tiền ròng"
          stroke="#6366f1"
          strokeWidth={2}
          dot={false}
        />
        <Area
          yAxisId="R"
          type="monotone"
          dataKey="Tích luỹ"
          stroke="#10b981"
          fill="url(#balGrad)"
          strokeWidth={2}
          dot={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
