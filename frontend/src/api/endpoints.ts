import { apiBlob, apiFetch } from "./client";
import type { CifSeed, EvaluateIn, EvaluateOut, ForecastOut, MetricsOut, ProfileIn } from "./types";

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

export function login(username: string, password: string): Promise<{ token: string }> {
  return apiFetch<{ token: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function getForecast(cif: string): Promise<ForecastOut> {
  return apiFetch<ForecastOut>(`/forecast/${cif}`);
}

export function getForecastChart(cif: string): Promise<Blob> {
  return apiBlob(`/forecast/${cif}/chart.png`);
}
