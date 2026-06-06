import type { ReactNode } from "react";

export function Metric({ label, value, hint }: { label: string; value: ReactNode; hint?: ReactNode }) {
  return (
    <div className="rounded-card border border-bnpl-surface-line/70 bg-white p-4 shadow-bnpl">
      <div className="font-mono text-xs font-medium uppercase tracking-[0.06em] text-bnpl-muted">{label}</div>
      <div className="mt-1 text-2xl font-extrabold tracking-normal text-bnpl-navy">{value}</div>
      {hint && <div className="mt-1 text-xs leading-5 text-bnpl-muted">{hint}</div>}
    </div>
  );
}
