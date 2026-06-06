import { type ReactNode, useState } from "react";
import { evaluatePurchase, explainPurchase, simulatePurchase } from "../../api/endpoints";
import type { EfrSafety, EvaluateOut, GoalImpactOut, ScenarioSimulationOut } from "../../api/types";
import { Button } from "../../components/ui/Button";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Field } from "../../components/ui/Field";
import { NumberInput } from "../../components/ui/NumberInput";
import { Spinner } from "../../components/ui/Spinner";
import { TextInput } from "../../components/ui/TextInput";
import { useAsync } from "../../hooks/useAsync";
import { formatVnd } from "../../lib/money";
import { CashflowChart } from "./CashflowChart";
import { ExplanationPanel } from "./ExplanationPanel";

// ── helpers ──────────────────────────────────────────────────────────────────

function optionLabel(id: string): string {
  if (/full/.test(id)) return "Trả thẳng";
  const m = id.match(/(\d+)/);
  return m ? `Trả góp ${m[1]} tháng` : id;
}

function parseOptionId(id: string): { type: "PAY_IN_FULL" | "INSTALLMENT"; term: number | null } {
  if (/full/.test(id)) return { type: "PAY_IN_FULL", term: null };
  const m = id.match(/(\d+)/);
  return { type: "INSTALLMENT", term: m ? Number(m[1]) : 6 };
}

// ── scenario narrative ────────────────────────────────────────────────────────

function buildNarrative(sim: ScenarioSimulationOut): string[] {
  const payMonths = sim.months.filter((m) => m.bnpl_payment > 0).length;
  const negMonths = sim.months.filter((m) => m.net_cashflow < 0).length;
  const first = sim.months[0];
  const afterPayoff = sim.months[payMonths] ?? null;
  const lines: string[] = [];

  if (payMonths <= 1) {
    const ncf = first?.net_cashflow ?? 0;
    lines.push(
      `Tháng đầu tiên: thanh toán ${formatVnd(first?.bnpl_payment ?? 0)} ngay lập tức. ` +
      `Dòng tiền ròng còn lại: ${formatVnd(ncf)}.`,
    );
    if (negMonths > 0) {
      lines.push("Dòng tiền âm tháng đầu — cần dùng đến quỹ dự phòng.");
    }
    lines.push("Từ tháng 2 trở đi: dòng tiền hoàn toàn bình thường, không còn gánh nặng BNPL.");
  } else {
    const bnplPay = first?.bnpl_payment ?? 0;
    const ncfDuring = first?.net_cashflow ?? 0;
    lines.push(
      `Tháng 1–${payMonths}: mỗi tháng trả ${formatVnd(bnplPay)} cho BNPL. ` +
      `Dòng tiền ròng còn lại ${formatVnd(ncfDuring)}/tháng.`,
    );
    if (negMonths > 0) {
      lines.push(`Có ${negMonths} tháng dòng tiền âm — cần kiểm soát chi tiêu cẩn thận.`);
    } else {
      lines.push("Dòng tiền luôn dương trong suốt thời gian trả góp.");
    }
    if (afterPayoff) {
      lines.push(
        `Tháng ${payMonths + 1} trở đi: khoản BNPL kết thúc, ` +
        `dòng tiền phục hồi lên ${formatVnd(afterPayoff.net_cashflow)}/tháng.`,
      );
    }
  }

  if (sim.total_interest === 0) {
    lines.push("Không phát sinh lãi suất — chi phí thực bằng đúng giá niêm yết.");
  } else {
    lines.push(`Lãi suất tổng cộng: ${formatVnd(sim.total_interest)} — đây là chi phí thực tế của việc trả góp.`);
  }

  return lines;
}

function riskDot(score: number) {
  if (score <= 30) return "bg-emerald-400";
  if (score <= 55) return "bg-amber-400";
  return "bg-red-500";
}

function riskText(score: number) {
  if (score <= 30) return "text-emerald-700";
  if (score <= 55) return "text-amber-700";
  return "text-red-700";
}

const EFR_CLASSES: Record<EfrSafety, string> = {
  SAFE:     "text-emerald-700 bg-emerald-50 border-emerald-200",
  WARNING:  "text-amber-700 bg-amber-50 border-amber-200",
  CRITICAL: "text-red-700 bg-red-50 border-red-200",
};

const EFR_LABEL: Record<EfrSafety, string> = {
  SAFE: "An toàn", WARNING: "Cảnh báo", CRITICAL: "Nguy hiểm",
};

// ── sub-components ───────────────────────────────────────────────────────────

function Cell({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <td className={`px-3 py-2.5 text-right text-sm ${className}`}>{children}</td>
  );
}

function ComparisonTable({
  data,
  selectedId,
  onSelect,
}: {
  data: EvaluateOut;
  selectedId: string;
  onSelect: (id: string) => void;
}) {
  const opts = data.options;

  // unique goals that have any impact across options
  const goalMap = new Map<string, string>();
  opts.forEach((o) => o.goal_impacts.forEach((gi) => goalMap.set(gi.goal_id, gi.goal_name)));

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
      <table className="w-full min-w-max border-collapse text-sm">
        <thead>
          <tr>
            <th className="w-36 border-b border-slate-100 px-3 py-3 text-left text-xs font-semibold text-slate-400">
              Chỉ số
            </th>
            {opts.map((o) => {
              const best = o.option_id === data.best_option_id;
              return (
                <th
                  key={o.option_id}
                  onClick={() => onSelect(o.option_id)}
                  className={`cursor-pointer border-b px-3 py-3 text-center text-xs font-semibold transition-colors ${
                    selectedId === o.option_id
                      ? "border-indigo-300 bg-indigo-50 text-indigo-700"
                      : "border-slate-100 text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  <div className="flex flex-col items-center gap-1">
                    {best && (
                      <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-[10px] font-bold text-indigo-600">
                        Khuyến nghị
                      </span>
                    )}
                    {optionLabel(o.option_id)}
                  </div>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {/* Risk score */}
          <MetricRow label="Điểm rủi ro">
            {opts.map((o) => (
              <Cell key={o.option_id}>
                <div className="flex items-center justify-end gap-1.5">
                  <span className={`h-2 w-2 rounded-full ${riskDot(o.risk_score)}`} />
                  <span className={`font-semibold ${riskText(o.risk_score)}`}>{o.risk_score}</span>
                </div>
              </Cell>
            ))}
          </MetricRow>

          {/* Monthly payment */}
          <MetricRow label="Trả / tháng">
            {opts.map((o) => (
              <Cell key={o.option_id} className="text-slate-700">
                {o.monthly_payment > 0 ? formatVnd(o.monthly_payment) : (
                  <span className="text-xs font-medium text-red-600">1 lần duy nhất</span>
                )}
              </Cell>
            ))}
          </MetricRow>

          {/* Total interest */}
          <MetricRow label="Tổng lãi phát sinh">
            {opts.map((o) => (
              <Cell key={o.option_id} className={o.total_interest > 0 ? "font-medium text-amber-700" : "text-slate-500"}>
                {formatVnd(o.total_interest)}
              </Cell>
            ))}
          </MetricRow>

          {/* NCF remaining */}
          <MetricRow label="NCF còn lại">
            {opts.map((o) => (
              <Cell key={o.option_id} className={`font-medium ${o.ncf_new < 0 ? "text-red-600" : "text-slate-700"}`}>
                {formatVnd(o.ncf_new)}
              </Cell>
            ))}
          </MetricRow>

          {/* DTI */}
          <MetricRow label="DTI mới">
            {opts.map((o) => (
              <Cell key={o.option_id} className={o.dti_new > 50 ? "font-medium text-red-600" : o.dti_new > 40 ? "text-amber-700" : "text-slate-700"}>
                {o.dti_new.toFixed(1)}%
              </Cell>
            ))}
          </MetricRow>

          {/* EFR safety */}
          <MetricRow label="Quỹ khẩn cấp">
            {opts.map((o) => (
              <Cell key={o.option_id}>
                <span className={`rounded border px-1.5 py-0.5 text-xs font-medium ${EFR_CLASSES[o.efr_safety]}`}>
                  {o.efr_after.toFixed(1)} th · {EFR_LABEL[o.efr_safety]}
                </span>
              </Cell>
            ))}
          </MetricRow>

          {/* Per-goal delay rows */}
          {[...goalMap.entries()].map(([goalId, goalName]) => (
            <MetricRow key={goalId} label={`Mục tiêu: ${goalName}`}>
              {opts.map((o) => {
                const gi: GoalImpactOut | undefined = o.goal_impacts.find((g) => g.goal_id === goalId);
                return (
                  <Cell key={o.option_id}>
                    {!gi ? (
                      <span className="text-slate-300">–</span>
                    ) : gi.delay_months > 0 ? (
                      <span className={`font-medium ${gi.reachable_by_deadline ? "text-amber-600" : "text-red-600"}`}>
                        +{gi.delay_months.toFixed(0)} tháng
                      </span>
                    ) : (
                      <span className="text-emerald-600">đúng hạn</span>
                    )}
                  </Cell>
                );
              })}
            </MetricRow>
          ))}

          {/* Flags */}
          <MetricRow label="Cảnh báo">
            {opts.map((o) => (
              <Cell key={o.option_id} className="text-xs text-red-500">
                {o.flags.length > 0 ? o.flags.join(", ") : <span className="text-slate-300">–</span>}
              </Cell>
            ))}
          </MetricRow>
        </tbody>
      </table>
    </div>
  );
}

function MetricRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <tr className="border-t border-slate-50 even:bg-slate-50/40">
      <td className="px-3 py-2.5 text-xs font-medium text-slate-500">{label}</td>
      {children}
    </tr>
  );
}

// ── main component ────────────────────────────────────────────────────────────

export function PurchaseEvaluator({ profileId }: { profileId: string }) {
  const [item, setItem]     = useState("");
  const [amount, setAmount] = useState(0);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showExplain, setShowExplain] = useState(false);

  const evalAsync    = useAsync(evaluatePurchase);
  const simAsync     = useAsync(simulatePurchase);
  const explainAsync = useAsync(explainPurchase);

  function runSim(optionId: string) {
    setSelectedId(optionId);
    const parsed = parseOptionId(optionId);
    simAsync.run({
      profile_id: profileId,
      purchase_amount: amount,
      option_type: parsed.type,
      term_months: parsed.term,
      apr: 0,
      horizon_months: 24,
      use_forecast: false,
    }).catch(() => undefined);
  }

  async function submit() {
    setShowExplain(false);
    const result = await evalAsync
      .run({ profile_id: profileId, item_name: item || "Món hàng", purchase_amount: amount, candidate_plans: null })
      .catch(() => null);
    if (result) runSim(result.best_option_id);
  }

  async function fetchExplain() {
    setShowExplain(true);
    await explainAsync
      .run({ profile_id: profileId, item_name: item || "Món hàng", purchase_amount: amount, candidate_plans: null })
      .catch(() => undefined);
  }

  const data = evalAsync.data;

  return (
    <div className="space-y-4">
      {evalAsync.error  && <ErrorBanner message={evalAsync.error} />}
      {simAsync.error   && <ErrorBanner message={simAsync.error} />}
      {explainAsync.error && <ErrorBanner message={explainAsync.error} />}

      {/* Input */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="mb-4 text-base font-semibold text-slate-800">Đánh giá khoản mua</h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <Field label="Tên sản phẩm / dịch vụ">
            <TextInput
              aria-label="Tên món hàng"
              placeholder="VD: Điện thoại iPhone"
              value={item}
              onChange={(e) => setItem(e.target.value)}
            />
          </Field>
          <Field label="Giá trị (₫)">
            <NumberInput ariaLabel="Giá" value={amount} onValueChange={setAmount} />
          </Field>
          <div className="flex items-end">
            <Button onClick={submit} disabled={evalAsync.loading || amount <= 0} className="w-full">
              {evalAsync.loading ? "Đang phân tích…" : "Phân tích ngay"}
            </Button>
          </div>
        </div>
      </div>

      {evalAsync.loading && <Spinner />}

      {data && (
        <>
          {/* Recommendation banner */}
          <div className="rounded-2xl border border-indigo-200 bg-indigo-50 px-5 py-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-indigo-400">
                  Tư vấn
                </p>
                <p className="mt-1 text-sm text-slate-700 leading-relaxed">
                  {data.balance_recommendation}
                </p>
              </div>
              <div className="flex-shrink-0 text-right">
                <p className="text-[11px] text-slate-400">Phân tích bởi</p>
                <p className="text-xs font-medium text-slate-500">{data.scorer_used}</p>
              </div>
            </div>
            <div className="mt-3 flex gap-2">
              <Button variant="ghost" onClick={fetchExplain} disabled={explainAsync.loading}>
                {explainAsync.loading ? "Đang giải thích…" : "Giải thích bằng ngôn ngữ thường"}
              </Button>
            </div>
          </div>

          {/* AI explanation */}
          {showExplain && explainAsync.loading && <Spinner />}
          {showExplain && explainAsync.data && <ExplanationPanel data={explainAsync.data} />}

          {/* Comparison table */}
          <ComparisonTable
            data={data}
            selectedId={selectedId ?? data.best_option_id}
            onSelect={runSim}
          />

          {/* Simulation chart for selected option */}
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold text-slate-700">
                  Dòng tiền 24 tháng —{" "}
                  <span className="text-indigo-600">
                    {selectedId ? optionLabel(selectedId) : ""}
                  </span>
                </p>
                <p className="mt-0.5 text-xs text-slate-400">
                  Nhấn vào cột trong bảng để xem kịch bản khác
                </p>
              </div>
              {simAsync.loading && (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
              )}
            </div>
            {simAsync.data?.months ? (
              <div className="mt-4">
                {/* Plain-language narrative */}
                <div className="mb-4 rounded-lg border border-indigo-100 bg-indigo-50 px-4 py-3">
                  <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-indigo-400">
                    Điều gì sẽ xảy ra nếu bạn chọn phương án này?
                  </p>
                  <ul className="space-y-1">
                    {buildNarrative(simAsync.data).map((line, i) => (
                      <li key={i} className="text-sm leading-relaxed text-slate-700">
                        {line.startsWith("Có ") || line.startsWith("Dòng tiền âm") ? (
                          <span className="text-amber-700">{line}</span>
                        ) : (
                          line
                        )}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="mb-4 grid grid-cols-3 gap-3 text-center text-xs">
                  <div className="rounded-lg bg-slate-50 p-2.5">
                    <p className="text-slate-400">Tổng chi phí BNPL</p>
                    <p className="mt-0.5 text-sm font-semibold text-slate-700">
                      {formatVnd(simAsync.data.total_bnpl_cost)}
                    </p>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-2.5">
                    <p className="text-slate-400">Tổng lãi</p>
                    <p className={`mt-0.5 text-sm font-semibold ${simAsync.data.total_interest > 0 ? "text-amber-700" : "text-slate-700"}`}>
                      {formatVnd(simAsync.data.total_interest)}
                    </p>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-2.5">
                    <p className="text-slate-400">Tháng NCF âm</p>
                    <p className={`mt-0.5 text-sm font-semibold ${simAsync.data.months.filter((m) => m.net_cashflow < 0).length > 0 ? "text-red-600" : "text-emerald-600"}`}>
                      {simAsync.data.months.filter((m) => m.net_cashflow < 0).length} / 24
                    </p>
                  </div>
                </div>
                <CashflowChart months={simAsync.data.months} />
                {simAsync.data.goal_impact_summary && (
                  <p className="mt-3 text-xs text-slate-500">{simAsync.data.goal_impact_summary}</p>
                )}
              </div>
            ) : !simAsync.loading ? (
              <p className="mt-4 text-sm text-slate-400">Chọn một phương án trong bảng để xem biểu đồ.</p>
            ) : null}
          </div>
        </>
      )}

      {/* Empty state */}
      {!data && !evalAsync.loading && (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-indigo-50">
            <svg className="h-6 w-6 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
          </div>
          <p className="text-sm font-medium text-slate-600">Nhập sản phẩm và giá trị để bắt đầu phân tích</p>
          <p className="mt-1 text-xs text-slate-400">
            Hệ thống sẽ so sánh các phương án thanh toán và ảnh hưởng đến mục tiêu tài chính của bạn
          </p>
        </div>
      )}
    </div>
  );
}
