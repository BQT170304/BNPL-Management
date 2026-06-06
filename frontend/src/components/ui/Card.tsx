import type { ReactNode } from "react";

export function Card({ title, children }: { title?: string; children: ReactNode }) {
  return (
    <div className="rounded-card border border-bnpl-surface-line/70 bg-bnpl-surface-card p-5 shadow-bnpl">
      {title && <h3 className="mb-3 font-mono text-xs font-semibold uppercase tracking-[0.08em] text-bnpl-muted">{title}</h3>}
      {children}
    </div>
  );
}
