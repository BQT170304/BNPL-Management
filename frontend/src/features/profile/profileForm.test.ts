// frontend/src/features/profile/profileForm.test.ts
import { describe, expect, it } from "vitest";
import { emptyForm, seedToForm, toProfileIn } from "./profileForm";

describe("profileForm", () => {
  it("emptyForm has a generated id and empty lists", () => {
    const f = emptyForm();
    expect(f.id).toMatch(/^p-/);
    expect(f.expenses).toEqual([]);
    expect(f.goals).toEqual([]);
  });

  it("toProfileIn builds the API body with numeric values", () => {
    const f = emptyForm();
    f.income.salary = 10_000_000;
    f.emergency_fund = 20_000_000;
    f.risk = "MEDIUM";
    f.expenses = [{ category: "rent", amount: 3_000_000, classification: "FIXED" }];
    f.goals = [
      { name: "Car", target_amount: 300_000_000, deadline: "2027-12-01",
        priority: "HIGH", savings_allocated: 0 },
    ];
    const body = toProfileIn(f);
    expect(body.id).toBe(f.id);
    expect(body.income.salary).toBe(10_000_000);
    expect(body.expenses[0].classification).toBe("FIXED");
    expect(body.goals[0].id).toMatch(/^g-/); // goal id generated
    expect(body.goals[0].target_amount).toBe(300_000_000);
  });

  it("seedToForm fills aggregate income/expense/debt", () => {
    const f = seedToForm({ cif: "100", income: 12_000_000, expense: 5_000_000, debt_payment: 2_000_000 });
    expect(f.income.salary).toBe(12_000_000);
    expect(f.expenses).toHaveLength(1);
    expect(f.expenses[0].amount).toBe(5_000_000);
    expect(f.expenses[0].classification).toBe("SEMI_FIXED");
    expect(f.debts).toHaveLength(1);
    expect(f.debts[0].monthly_payment).toBe(2_000_000);
  });
});
