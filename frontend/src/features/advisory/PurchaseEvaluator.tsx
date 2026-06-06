// frontend/src/features/advisory/PurchaseEvaluator.tsx
import { useState } from "react";
import { evaluatePurchase } from "../../api/endpoints";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Field } from "../../components/ui/Field";
import { NumberInput } from "../../components/ui/NumberInput";
import { TextInput } from "../../components/ui/TextInput";
import { useAsync } from "../../hooks/useAsync";
import { riskClass } from "../../lib/bands";
import { formatVnd } from "../../lib/money";

export function PurchaseEvaluator({ profileId }: { profileId: string }) {
  const [item, setItem] = useState("");
  const [amount, setAmount] = useState(0);
  const { run, data, loading, error } = useAsync(evaluatePurchase);

  async function submit() {
    await run({
      profile_id: profileId, item_name: item || "Món hàng",
      purchase_amount: amount, candidate_plans: null,
    }).catch(() => undefined);
  }

  const ranked = data
    ? [...data.options].sort((a, b) => Number(b.recommended) - Number(a.recommended) || a.risk_score - b.risk_score)
    : [];

  return (
    <div className="space-y-4">
      {error && <ErrorBanner message={error} />}
      <Card title="Khoản mua mới">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <Field label="Tên món hàng">
            <TextInput aria-label="Tên món hàng" value={item}
              onChange={(e) => setItem(e.target.value)} />
          </Field>
          <Field label="Giá (₫)">
            <NumberInput ariaLabel="Giá" value={amount} onValueChange={setAmount} />
          </Field>
          <div className="flex items-end">
            <Button onClick={submit} disabled={loading || amount <= 0}>
              {loading ? "Đang đánh giá…" : "Đánh giá"}
            </Button>
          </div>
        </div>
      </Card>

      {data && (
        <Card title="Kết quả">
          <p className="text-sm text-slate-700">
            <strong>Đề xuất:</strong> {data.summary}{" "}
            <span className="ml-2 rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
              nguồn điểm: {data.scorer_used}
            </span>
          </p>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {ranked.map((o) => (
          <div key={o.option_id}
            className={`rounded-xl border bg-white p-4 ${o.option_id === data?.best_option_id ? "border-indigo-400 ring-1 ring-indigo-200" : "border-slate-200"}`}>
            <div className="flex items-center justify-between">
              <span className="font-semibold">{o.option_id}</span>
              <Badge className={riskClass(o.risk_score)}>Rủi ro {o.risk_score.toFixed(0)}</Badge>
            </div>
            <p className="mt-2 text-sm text-slate-600">{o.explanation}</p>
            <dl className="mt-3 grid grid-cols-2 gap-1 text-xs text-slate-500">
              <dt>Trả/tháng</dt><dd className="text-right text-slate-700">{formatVnd(o.monthly_payment)}</dd>
              <dt>NCF mới</dt><dd className="text-right text-slate-700">{formatVnd(o.ncf_new)}</dd>
              <dt>DTI mới</dt><dd className="text-right text-slate-700">{o.dti_new.toFixed(1)}%</dd>
              <dt>EFR sau</dt><dd className="text-right text-slate-700">{o.efr_after.toFixed(2)}</dd>
              <dt>ΔPGRS</dt><dd className="text-right text-slate-700">{o.delta_pgrs.toFixed(1)}</dd>
            </dl>
            {o.flags.length > 0 && (
              <div className="mt-2 text-xs font-medium text-red-600">{o.flags.join(", ")}</div>
            )}
            {!o.recommended && (
              <div className="mt-1 text-xs text-slate-400">Không khuyến nghị</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
