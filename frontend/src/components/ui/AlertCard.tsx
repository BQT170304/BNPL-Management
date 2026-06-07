import type { AlertOut } from "../../api/types";

const LEVEL_STYLES: Record<string, string> = {
  CRITICAL: "border-red-300 bg-red-50 text-red-800",
  WARNING: "border-amber-300 bg-amber-50 text-amber-800",
  INFO: "border-blue-200 bg-blue-50 text-blue-800",
};
const LEVEL_DOT: Record<string, string> = {
  CRITICAL: "bg-red-500",
  WARNING: "bg-amber-500",
  INFO: "bg-blue-400",
};

export function AlertCard({ alert }: { alert: AlertOut }) {
  return (
    <div className={`rounded-lg border px-4 py-3 text-sm ${LEVEL_STYLES[alert.level] ?? LEVEL_STYLES.INFO}`}>
      <div className="flex items-start gap-2">
        <span className={`mt-1.5 h-2 w-2 flex-shrink-0 rounded-full ${LEVEL_DOT[alert.level]}`} />
        <div>
          <p className="font-medium">{alert.message}</p>
          <p className="mt-0.5 opacity-80">{alert.recommendation}</p>
        </div>
      </div>
    </div>
  );
}
