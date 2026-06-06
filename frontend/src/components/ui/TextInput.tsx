import type { InputHTMLAttributes } from "react";

export function TextInput(props: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      type="text"
      {...props}
      className={`min-h-12 w-full rounded-lg border border-bnpl-surface-line bg-white px-3 py-2 text-sm text-bnpl-ink placeholder:text-bnpl-muted/50 focus:border-bnpl-navy focus:outline-none focus:ring-2 focus:ring-bnpl-orange/20 ${props.className ?? ""}`}
    />
  );
}
