import { apiFetch } from "./client";
import type { CifSeed, EvaluateIn, EvaluateOut, MetricsOut, ProfileIn } from "./types";

export function createProfile(body: ProfileIn): Promise<{ id: string }> {
  return apiFetch<{ id: string }>("/profiles", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getAnalysis(profileId: string): Promise<MetricsOut> {
  return apiFetch<MetricsOut>(`/profiles/${profileId}/analysis`);
}

export function evaluatePurchase(body: EvaluateIn): Promise<EvaluateOut> {
  return apiFetch<EvaluateOut>("/advisory/evaluate", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function listCifs(): Promise<string[]> {
  return apiFetch<{ cifs: string[] }>("/ingestion/cifs").then((r) => r.cifs);
}

export function getCifSeed(cif: string, strategy: "latest" | "average"): Promise<CifSeed> {
  return apiFetch<CifSeed>(`/ingestion/cif/${cif}/seed?strategy=${strategy}`);
}
