import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { EvaluateOut, ScenarioSimulationOut } from "../../api/types";
import { PurchaseEvaluator } from "./PurchaseEvaluator";

afterEach(() => vi.restoreAllMocks());

const SIM: ScenarioSimulationOut = {
  option_id: "installment_12", label: "Trả góp 12 tháng",
  months: [], total_bnpl_cost: 15_000_000, total_interest: 0,
  break_even_month: null, goal_impact_summary: "", risk_level: "LOW",
};

const RESULT: EvaluateOut = {
  best_option_id: "installment_12",
  summary: "Nên trả góp 12 tháng",
  scorer_used: "hard_rules",
  balance_recommendation: "Phương án trả góp 12 tháng là cân bằng nhất.",
  options: [
    {
      option_id: "installment_12", risk_score: 45, recommended: true,
      explanation: "Bảo toàn dòng tiền", key_factors: ["dòng tiền"],
      monthly_payment: 1_250_000, ncf_new: -50_000, dti_new: 46.5,
      efr_after: 2.94, delta_pgrs: 8, flags: [],
      efr_safety: "WARNING", total_interest: 0, goal_impacts: [],
    },
    {
      option_id: "pay_in_full", risk_score: 80, recommended: false,
      explanation: "Âm dòng tiền", key_factors: [],
      monthly_payment: 0, ncf_new: -13_800_000, dti_new: 37.9,
      efr_after: 0.64, delta_pgrs: 0, flags: ["NEGATIVE_CASHFLOW"],
      efr_safety: "CRITICAL", total_interest: 0, goal_impacts: [],
    },
  ],
};

describe("PurchaseEvaluator", () => {
  it("evaluates and renders comparison table with human-readable labels", async () => {
    vi.stubGlobal("fetch", vi.fn(async (url: unknown) =>
      new Response(
        JSON.stringify((url as string).includes("simulate") ? SIM : RESULT),
        { status: 200 },
      )));
    render(<PurchaseEvaluator profileId="p1" />);

    await userEvent.type(screen.getByLabelText(/tên món/i), "Điện thoại");
    await userEvent.type(screen.getByLabelText(/giá/i), "15.000.000");
    await userEvent.click(screen.getByRole("button", { name: /phân tích/i }));

    await waitFor(() =>
      expect(screen.getByText(/Phương án trả góp 12 tháng/)).toBeInTheDocument()
    );
    expect(screen.getAllByText("Trả góp 12 tháng").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Thanh toán 1 lần").length).toBeGreaterThan(0);
    expect(screen.getByText(/Dòng tiền âm/)).toBeInTheDocument();
  });
});
