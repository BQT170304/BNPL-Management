import type { ReactNode } from "react";

export function Card({ title, children }: { title?: string; children: ReactNode }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      {title && <h3 className="mb-3 text-sm font-semibold text-slate-500">{title}</h3>}
      {children}
    </div>
  );
}
