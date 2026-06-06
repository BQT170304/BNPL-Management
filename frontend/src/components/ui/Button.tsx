import type { ButtonHTMLAttributes } from "react";

export function Button({
  variant = "primary",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "ghost" }) {
  const base =
    "inline-flex items-center justify-center rounded-lg px-4 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50";
  const styles =
    variant === "primary"
      ? "bg-bnpl-navy text-white shadow-bnpl hover:bg-bnpl-navy-soft focus:outline-none focus:ring-2 focus:ring-bnpl-orange/40"
      : "border border-bnpl-surface-line bg-white text-bnpl-navy hover:border-bnpl-orange/50 hover:text-bnpl-orange focus:outline-none focus:ring-2 focus:ring-bnpl-orange/30";
  return <button className={`${base} ${styles} ${className}`} {...props} />;
}
