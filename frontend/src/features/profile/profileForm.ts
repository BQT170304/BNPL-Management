import type {
  AssetIn, Classification, DebtIn, ExpenseIn, ProfileIn, Risk,
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
  income: ProfileIn["income"];
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
  return `${prefix}-${counter}-${Math.abs(counter * 2654435761)}`;
}

function isoInMonths(n: number): string {
  const d = new Date();
  d.setMonth(d.getMonth() + n);
  return d.toISOString().slice(0, 10);
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

  // split total expense into meaningful categories
  const ex = seed.expense;
  f.expenses = [
    { category: "Nhà ở & tiện ích",        amount: Math.round(ex * 0.35), classification: "FIXED" as Classification },
    { category: "Ăn uống & sinh hoạt",      amount: Math.round(ex * 0.35), classification: "SEMI_FIXED" as Classification },
    { category: "Đi lại & liên lạc",        amount: Math.round(ex * 0.15), classification: "SEMI_FIXED" as Classification },
    { category: "Giải trí & mua sắm",       amount: Math.round(ex * 0.15), classification: "DISCRETIONARY" as Classification },
  ];

  if (seed.debt_payment > 0) {
    f.debts = [{
      name: "Khoản nợ hiện tại",
      monthly_payment: seed.debt_payment,
      balance: null, apr: 0, months_remaining: null, debt_type: "INSTALLMENT",
    }];
  }

  // emergency fund = 2 months of essential expenses
  f.emergency_fund = Math.round(ex * 0.7 * 2);

  // default goals so analysis is meaningful
  const monthlySavings = Math.max(0, seed.income - seed.expense - seed.debt_payment);
  f.goals = [
    {
      name: "Quỹ khẩn cấp 6 tháng",
      target_amount: Math.round(ex * 0.7 * 6),
      deadline: isoInMonths(18),
      priority: "VERY_HIGH",
      savings_allocated: Math.round(monthlySavings * 0.35),
    },
    {
      name: "Du lịch / kỳ nghỉ",
      target_amount: 20_000_000,
      deadline: isoInMonths(12),
      priority: "MEDIUM",
      savings_allocated: Math.round(monthlySavings * 0.1),
    },
    {
      name: "Dự phòng mua sắm lớn",
      target_amount: 50_000_000,
      deadline: isoInMonths(36),
      priority: "LOW",
      savings_allocated: Math.round(monthlySavings * 0.15),
    },
  ];

  return f;
}

export function profileToForm(profile: ProfileIn): ProfileFormState {
  return {
    id: profile.id,
    income: { ...profile.income },
    risk: profile.risk,
    emergency_fund: profile.emergency_fund,
    expenses: profile.expenses.map((e) => ({ ...e, classification: e.classification as Classification })),
    debts: profile.debts.map((d) => ({ ...d })),
    assets: profile.assets.map((a) => ({ ...a })),
    goals: profile.goals.map((g) => ({
      name: g.name,
      target_amount: g.target_amount,
      deadline: typeof g.deadline === "string" ? g.deadline : String(g.deadline),
      priority: g.priority,
      savings_allocated: g.savings_allocated,
    })),
  };
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
