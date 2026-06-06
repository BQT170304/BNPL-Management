export type Classification = "FIXED" | "SEMI_FIXED" | "DISCRETIONARY";
export type DebtType = "REVOLVING" | "INSTALLMENT" | "SECURED";
export type AssetType = "CASH" | "SAVINGS" | "OTHER";
export type Liquidity = "HIGH" | "MEDIUM" | "LOW";
export type Risk = "LOW" | "MEDIUM" | "HIGH";
export type Priority = "LOW" | "MEDIUM" | "HIGH" | "VERY_HIGH";
export type DtiBand = "SAFE" | "ACCEPTABLE" | "WARNING" | "DANGER";

export interface IncomeIn {
  salary: number;
  secondary: number;
  avg_bonus_monthly: number;
  passive: number;
}
export interface ExpenseIn {
  category: string;
  amount: number;
  classification: Classification;
}
export interface DebtIn {
  name: string;
  monthly_payment: number;
  balance: number | null;
  apr: number;
  months_remaining: number | null;
  debt_type: DebtType;
}
export interface AssetIn {
  type: AssetType;
  value: number;
  liquidity: Liquidity;
}
export interface GoalIn {
  id: string;
  name: string;
  target_amount: number;
  deadline: string; // YYYY-MM-DD
  priority: Priority;
  savings_allocated: number;
}
export interface ProfileIn {
  id: string;
  income: IncomeIn;
  risk: Risk;
  emergency_fund: number;
  expenses: ExpenseIn[];
  debts: DebtIn[];
  assets: AssetIn[];
  goals: GoalIn[];
}

export interface GoalMetricOut {
  goal_id: string;
  name: string;
  gap: number;
  monthly_allocated: number;
  gat: number;
  delay: number;
  grs: number;
  months_remaining: number;
}
export interface MetricsOut {
  ncf: number;
  dti: number;
  dti_band: DtiBand;
  saving_rate: number;
  efr: number;
  pgrs: number;
  goals: GoalMetricOut[];
  flags: string[];
}

export interface PlanIn {
  type: "PAY_IN_FULL" | "INSTALLMENT";
  months: number | null;
  apr: number;
}
export interface EvaluateIn {
  profile_id: string;
  item_name: string;
  purchase_amount: number;
  candidate_plans: PlanIn[] | null;
}
export interface OptionScoreOut {
  option_id: string;
  risk_score: number;
  recommended: boolean;
  explanation: string;
  key_factors: string[];
  monthly_payment: number;
  ncf_new: number;
  dti_new: number;
  efr_after: number;
  delta_pgrs: number;
  flags: string[];
}
export interface EvaluateOut {
  best_option_id: string;
  summary: string;
  scorer_used: string;
  options: OptionScoreOut[];
}

export interface CifSeed {
  cif: string;
  income: number;
  expense: number;
  debt_payment: number;
}

export interface TokenOut { token: string; }
export interface HistoryPointOut { ds: string; y: number; }
export interface ForecastPointOut { ds: string; yhat: number; lower: number; upper: number; }
export interface ForecastOut {
  cif: string;
  next_30_net: number;
  next_90_net: number;
  history: HistoryPointOut[];
  forecast: ForecastPointOut[];
}
