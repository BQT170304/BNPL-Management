import { useRef, useState } from "react";
import { extractProfile, type ExtractResponse } from "../../api/endpoints";
import type { ProfileIn } from "../../api/types";
import { Button } from "../../components/ui/Button";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";
import { formatVnd } from "../../lib/money";

function SummaryRow({ label, value, highlight }: { label: string; value: string; highlight?: "green" | "red" }) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-slate-100 last:border-0">
      <span className="text-sm text-slate-500">{label}</span>
      <span className={`text-sm font-semibold ${
        highlight === "green" ? "text-emerald-600" :
        highlight === "red" ? "text-red-600" : "text-slate-700"
      }`}>{value}</span>
    </div>
  );
}

export function TransactionImport({
  onExtracted,
}: {
  onExtracted: (profile: ProfileIn, cif?: string) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ExtractResponse | null>(null);

  async function handleFile(file: File) {
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const r = await extractProfile(file);
      setResult(r);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Không đọc được file");
    } finally {
      setLoading(false);
    }
  }

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  return (
    <div className="space-y-4">
      {error && <ErrorBanner message={error} />}

      {/* Drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        onClick={() => inputRef.current?.click()}
        className="cursor-pointer rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 px-6 py-8 text-center hover:border-indigo-400 hover:bg-indigo-50/40 transition-colors"
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          className="hidden"
          onChange={handleInputChange}
        />
        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-white shadow-sm border border-slate-200">
          <svg className="h-6 w-6 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        {loading ? (
          <div className="flex justify-center"><Spinner /></div>
        ) : (
          <>
            <p className="text-sm font-medium text-slate-700">Tải lên file giao dịch</p>
            <p className="mt-1 text-xs text-slate-400">CSV hoặc Excel (.csv, .xlsx) — định dạng: CIF_NO, NOTE, TRAN_DATE, AMOUNT</p>
          </>
        )}
      </div>

      {/* Extracted summary */}
      {result && (
        <div className="rounded-xl border border-emerald-200 bg-white">
          <div className="border-b border-slate-100 px-4 py-3">
            <p className="text-sm font-semibold text-slate-700">Kết quả phân tích ({result.summary.months_analyzed} tháng)</p>
            {result.summary.cif && (
              <p className="text-xs text-slate-400 mt-0.5">CIF: {result.summary.cif}</p>
            )}
          </div>
          <div className="px-4 py-3 space-y-0">
            <SummaryRow label="Thu nhập trung bình / tháng" value={formatVnd(result.summary.avg_monthly_income)} highlight="green" />
            <SummaryRow label="Chi tiêu trung bình / tháng" value={formatVnd(result.summary.avg_monthly_expense)} />
            <SummaryRow
              label="Tiền còn lại / tháng"
              value={formatVnd(result.summary.avg_monthly_net)}
              highlight={result.summary.avg_monthly_net >= 0 ? "green" : "red"}
            />
          </div>
          <div className="border-t border-slate-100 px-4 py-3">
            <p className="text-xs text-slate-400 mb-3">
              Hệ thống đã tự động phân loại các khoản thu chi. Bạn có thể xem lại và chỉnh sửa ở bước tiếp theo.
            </p>
            <Button onClick={() => onExtracted(result.suggested_profile, result.summary.cif || undefined)} className="w-full">
              Xem lại & Lưu hồ sơ →
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
