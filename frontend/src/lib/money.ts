// frontend/src/lib/money.ts
export function formatVnd(amount: number): string {
  const sign = amount < 0 ? "-" : "";
  const digits = Math.abs(Math.round(amount)).toString();
  const grouped = digits.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `${sign}${grouped} ₫`;
}

export function parseVnd(input: string): number {
  const digits = input.replace(/[^\d]/g, "");
  return digits ? Number.parseInt(digits, 10) : 0;
}
