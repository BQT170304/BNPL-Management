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
      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
    />
  );
}
