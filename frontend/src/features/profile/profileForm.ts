// frontend/src/features/profile/profileForm.ts
import type {
  AssetIn, Classification, DebtIn, ExpenseIn, IncomeIn,
  ProfileIn, Risk,
} from "../../api/types";
import type { CifSeed } from "../../api/types";

export interface GoalFormRow {
  name: string;
  target_amount: number;
  deadline: string;
  priority: ProfileIn["goals"][number]["priority"];
  savings_allocated: number;
}

export interface ProfileFormState {
  id: string;
  income: IncomeIn;
  risk: Risk;
  emergency_fund: number;
  expenses: ExpenseIn[];
  debts: DebtIn[];
  assets: AssetIn[];
  goals: GoalFormRow[];
}

let counter = 0;
function uid(prefix: string): string {
  counter += 1;
  return `${prefix}-${counter}-${Math.abs(hashNow())}`;
}
function hashNow(): number {
  // deterministic-enough unique suffix without Date.now in tests:
  // use a monotonically increasing counter combined with a fixed salt
  return counter * 2654435761;
}

export function emptyForm(): ProfileFormState {
  return {
    id: uid("p"),
    income: { salary: 0, secondary: 0, avg_bonus_monthly: 0, passive: 0 },
    risk: "MEDIUM",
    emergency_fund: 0,
    expenses: [],
    debts: [],
    assets: [],
    goals: [],
  };
}

export function seedToForm(seed: CifSeed): ProfileFormState {
  const f = emptyForm();
  f.income.salary = seed.income;
  const semiFixed: Classification = "SEMI_FIXED";
  f.expenses = [
    { category: "Tổng chi tiêu (từ CIF)", amount: seed.expense, classification: semiFixed },
  ];
  f.debts = [
    {
      name: "Tổng nợ (từ CIF)", monthly_payment: seed.debt_payment, balance: null,
      apr: 0, months_remaining: null, debt_type: "INSTALLMENT",
    },
  ];
  return f;
}

export function toProfileIn(form: ProfileFormState): ProfileIn {
  return {
    id: form.id,
    income: { ...form.income },
    risk: form.risk,
    emergency_fund: form.emergency_fund,
    expenses: form.expenses.map((e) => ({ ...e })),
    debts: form.debts.map((d) => ({ ...d })),
    assets: form.assets.map((a) => ({ ...a })),
    goals: form.goals.map((g) => ({ id: uid("g"), ...g })),
  };
}
