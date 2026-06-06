// frontend/src/lib/bands.ts
import type { DtiBand } from "../api/types";

const BADGE = "px-2 py-0.5 rounded-full text-xs font-medium";

export function dtiBandClass(band: DtiBand): string {
  const map: Record<DtiBand, string> = {
    SAFE: "bg-green-100 text-green-800",
    ACCEPTABLE: "bg-blue-100 text-blue-800",
    WARNING: "bg-amber-100 text-amber-800",
    DANGER: "bg-red-100 text-red-800",
  };
  return `${BADGE} ${map[band]}`;
}

export function riskClass(score: number): string {
  if (score <= 25) return `${BADGE} bg-green-100 text-green-800`;
  if (score <= 50) return `${BADGE} bg-blue-100 text-blue-800`;
  if (score <= 75) return `${BADGE} bg-amber-100 text-amber-800`;
  return `${BADGE} bg-red-100 text-red-800`;
}
