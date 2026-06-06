import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { ForecastOut } from "../../api/types";
import { CashflowForecast } from "./CashflowForecast";

afterEach(() => {
  vi.restoreAllMocks();
  localStorage.clear();
});

const FORECAST: ForecastOut = {
  cif: "10000327",
  next_30_net: 1_234_567.4,
  next_90_net: 3_700_000.6,
  history: [{ ds: "2026-05-01", y: 1_000_000 }],
  forecast: [{ ds: "2026-06-01", yhat: 1_200_000, lower: 900_000, upper: 1_500_000 }],
};

describe("CashflowForecast", () => {
  it("renders summary metrics and the chart image", async () => {
    vi.stubGlobal("URL", {
      ...URL,
      createObjectURL: vi.fn(() => "blob:mock"),
      revokeObjectURL: vi.fn(),
    });

    vi.stubGlobal("fetch", vi.fn(async (url: string) => {
      if (url.includes("/chart.png")) {
        return new Response(new Blob(["png-bytes"]), { status: 200 });
      }
      return new Response(JSON.stringify(FORECAST), { status: 200 });
    }));

    render(<CashflowForecast />);

    await waitFor(() =>
      expect(screen.getByText(/1\.234\.567 ₫/)).toBeInTheDocument());
    expect(screen.getByText(/3\.700\.001 ₫/)).toBeInTheDocument();

    await waitFor(() =>
      expect(screen.getByRole("img", { name: /biểu đồ dự báo/i })).toHaveAttribute(
        "src",
        "blob:mock",
      ));
  });
});
