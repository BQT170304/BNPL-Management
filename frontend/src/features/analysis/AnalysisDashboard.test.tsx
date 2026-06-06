// frontend/src/features/analysis/AnalysisDashboard.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { MetricsOut } from "../../api/types";
import { AnalysisDashboard } from "./AnalysisDashboard";

afterEach(() => vi.restoreAllMocks());

const METRICS: MetricsOut = {
  ncf: 1_200_000, dti: 37.93, dti_band: "WARNING", saving_rate: 8.28,
  efr: 2.94, pgrs: 100,
  goals: [{ goal_id: "g1", name: "Car", gap: 300_000_000, monthly_allocated: 400_000,
            gat: 750, delay: 720, grs: 100, months_remaining: 30 }],
  flags: [],
};

describe("AnalysisDashboard", () => {
  it("renders metrics from the API", async () => {
    vi.stubGlobal("fetch", vi.fn(async () =>
      new Response(JSON.stringify(METRICS), { status: 200 })));
    render(<AnalysisDashboard profileId="p1" />);
    await waitFor(() => expect(screen.getByText(/1\.200\.000 ₫/)).toBeInTheDocument());
    expect(screen.getByText("WARNING")).toBeInTheDocument();
    expect(screen.getByText("Car")).toBeInTheDocument();
  });

  it("shows an error banner on failure", async () => {
    vi.stubGlobal("fetch", vi.fn(async () =>
      new Response(JSON.stringify({ detail: "Profile not found: p1" }), { status: 404 })));
    render(<AnalysisDashboard profileId="p1" />);
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent(/not found/i));
  });
});
