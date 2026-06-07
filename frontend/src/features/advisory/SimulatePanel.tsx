import { useState } from "react";
import { simulatePurchase } from "../../api/endpoints";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Field } from "../../components/ui/Field";
import { Metric } from "../../components/ui/Metric";
import { NumberInput } from "../../components/ui/NumberInput";
import { Select } from "../../components/ui/Select";

const OPTION_TYPE_OPTIONS = [
  { value: "INSTALLMENT", label: "Trả góp" },
  { value: "PAY_IN_FULL", label: "Trả thẳng" },
];
const TERM_OPTIONS = [
  { value: "3", label: "3 tháng" },
  { value: "6", label: "6 tháng" },
  { value: "12", label: "12 tháng" },
];
import { Spinner } from "../../components/ui/Spinner";
import { useAsync } from "../../hooks/useAsync";
import { formatVnd } from "../../lib/money";
import { CashflowChart } from "./CashflowChart";

const RISK_STYLES: Record<string, string> = {
  LOW: "text-green-700 bg-green-50 border-green-200",
  MEDIUM: "text-amber-700 bg-amber-50 border-amber-200",
  HIGH: "text-red-700 bg-red-50 border-red-200",
};

export function SimulatePanel({ profileId }: { profileId: string }) {
  const [amount, setAmount] = useState(0);
  const [optionType, setOptionType] = useState<"PAY_IN_FULL" | "INSTALLMENT">("INSTALLMENT");
  const [termMonths, setTermMonths] = useState(6);
  const { run, data, loading, error } = useAsync(simulatePurchase);

  async function submit() {
    await run({
      profile_id: profileId,
      purchase_amount: amount,
      option_type: optionType,
      term_months: optionType === "INSTALLMENT" ? termMonths : null,
      apr: 0,
      horizon_months: 24,
      use_forecast: false,
    }).catch(() => undefined);
  }

  const negMonths = data ? data.months.filter((m) => m.net_cashflow < 0).length : 0;

  return (
    <div className="space-y-4">
      {error && <ErrorBanner message={error} />}
      <Card title="Mô phỏng dòng tiền">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
          <Field label="Số tiền mua (₫)">
            <NumberInput ariaLabel="Số tiền" value={amount} onValueChange={setAmount} />
          </Field>
          <Field label="Hình thức">
            <Select
              options={OPTION_TYPE_OPTIONS}
              value={optionType}
              onChange={(e) => setOptionType(e.target.value as "PAY_IN_FULL" | "INSTALLMENT")}
            />
          </Field>
          {optionType === "INSTALLMENT" && (
            <Field label="Kỳ hạn (tháng)">
              <Select
                options={TERM_OPTIONS}
                value={String(termMonths)}
                onChange={(e) => setTermMonths(Number(e.target.value))}
              />
            </Field>
          )}
          <div className="flex items-end">
            <Button onClick={submit} disabled={loading || amount <= 0}>
              {loading ? "Đang tính…" : "Mô phỏng"}
            </Button>
          </div>
        </div>
      </Card>

      {loading && <Spinner />}

      {data && (
        <>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Metric label="Tổng chi phí" value={formatVnd(data.total_bnpl_cost)} />
            <Metric label="Tổng lãi" value={formatVnd(data.total_interest)} />
            <Metric label="Tháng NCF âm" value={`${negMonths}/24`}
              hint={negMonths === 0 ? "Không có" : `${negMonths} tháng thiếu tiền`} />
            <Metric label="Break-even" value={data.break_even_month !== null ? `Tháng ${data.break_even_month + 1}` : "Chưa hồi phục"} />
          </div>

          <div className={`rounded-lg border px-4 py-2 text-sm font-medium ${RISK_STYLES[data.risk_level]}`}>
            Mức rủi ro: {data.risk_level} — {data.goal_impact_summary}
          </div>

          <Card title="Dòng tiền ròng & số dư tích luỹ (24 tháng)">
            <CashflowChart months={data.months} />
          </Card>

          <Card title="Chi tiết theo tháng">
            <div className="max-h-64 overflow-y-auto">
              <table className="w-full text-xs">
                <thead className="sticky top-0 bg-white">
                  <tr className="text-left text-slate-500">
                    <th className="py-1">Tháng</th>
                    <th className="text-right">BNPL</th>
                    <th className="text-right">NCF</th>
                    <th className="text-right">Tích luỹ</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {data.months.map((m) => (
                    <tr key={m.month} className={`border-t border-slate-100 ${m.net_cashflow < 0 ? "bg-red-50" : ""}`}>
                      <td className="py-1">{m.year_month}</td>
                      <td className="text-right">{formatVnd(m.bnpl_payment)}</td>
                      <td className={`text-right font-medium ${m.net_cashflow < 0 ? "text-red-600" : "text-green-700"}`}>
                        {formatVnd(Math.round(m.net_cashflow))}
                      </td>
                      <td className={`text-right ${m.cumulative_balance < 0 ? "text-red-600" : ""}`}>
                        {formatVnd(Math.round(m.cumulative_balance))}
                      </td>
                      <td className="pl-2 text-red-500">{m.warning ? "⚠" : ""}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
