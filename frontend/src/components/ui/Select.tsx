import type { SelectHTMLAttributes } from "react";

export function Select({
  options,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement> & { options: { value: string; label: string }[] }) {
  return (
    <select
      {...props}
      className={`min-h-12 w-full rounded-lg border border-bnpl-surface-line bg-white px-3 py-2 text-sm text-bnpl-ink focus:border-bnpl-navy focus:outline-none focus:ring-2 focus:ring-bnpl-orange/20 ${props.className ?? ""}`}
    >
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  );
}
