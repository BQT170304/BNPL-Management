import type { ReactNode } from "react";

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block font-mono text-xs font-medium uppercase tracking-[0.06em] text-bnpl-muted">{label}</span>
      {children}
    </label>
  );
}
