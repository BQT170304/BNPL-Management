// frontend/src/features/advisory/PurchaseEvaluator.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { EvaluateOut } from "../../api/types";
import { PurchaseEvaluator } from "./PurchaseEvaluator";

afterEach(() => vi.restoreAllMocks());

const RESULT: EvaluateOut = {
  best_option_id: "installment_12", summary: "Nên trả góp 12 tháng",
  scorer_used: "deterministic",
  options: [
    { option_id: "installment_12", risk_score: 45, recommended: true,
      explanation: "Bảo toàn dòng tiền", key_factors: ["dòng tiền"], monthly_payment: 1_250_000,
      ncf_new: -50_000, dti_new: 46.5, efr_after: 2.94, delta_pgrs: 8, flags: [] },
    { option_id: "full", risk_score: 80, recommended: false,
      explanation: "Âm dòng tiền", key_factors: [], monthly_payment: 0,
      ncf_new: -13_800_000, dti_new: 37.9, efr_after: 0.64, delta_pgrs: 0,
      flags: ["NEGATIVE_CASHFLOW"] },
  ],
};

describe("PurchaseEvaluator", () => {
  it("evaluates and renders ranked options", async () => {
    vi.stubGlobal("fetch", vi.fn(async () =>
      new Response(JSON.stringify(RESULT), { status: 200 })));
    render(<PurchaseEvaluator profileId="p1" />);

    await userEvent.type(screen.getByLabelText(/tên món/i), "Điện thoại");
    await userEvent.type(screen.getByLabelText(/giá/i), "15.000.000");
    await userEvent.click(screen.getByRole("button", { name: /đánh giá/i }));

    await waitFor(() => expect(screen.getByText(/Nên trả góp 12 tháng/)).toBeInTheDocument());
    expect(screen.getByText("installment_12")).toBeInTheDocument();
    expect(screen.getByText(/NEGATIVE_CASHFLOW/)).toBeInTheDocument();
  });
});
