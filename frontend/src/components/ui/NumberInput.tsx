import { parseVnd, formatVnd } from "../../lib/money";

export function NumberInput({
  value,
  onValueChange,
  ariaLabel,
}: {
  value: number;
  onValueChange: (v: number) => void;
  ariaLabel?: string;
}) {
  return (
    <input
      type="text"
      inputMode="numeric"
      aria-label={ariaLabel}
      value={value === 0 ? "" : formatVnd(value).replace(" ₫", "")}
      onChange={(e) => onValueChange(parseVnd(e.target.value))}
      placeholder="0"
      className="min-h-12 w-full rounded-lg border border-bnpl-surface-line bg-white px-3 py-2 font-mono text-sm text-bnpl-ink placeholder:text-bnpl-muted/50 focus:border-bnpl-navy focus:outline-none focus:ring-2 focus:ring-bnpl-orange/20"
    />
  );
}
