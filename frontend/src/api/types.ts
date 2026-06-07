export type Classification = "FIXED" | "SEMI_FIXED" | "DISCRETIONARY";
export type DebtType = "REVOLVING" | "INSTALLMENT" | "SECURED";
export type AssetType = "CASH" | "SAVINGS" | "OTHER";
export type Liquidity = "HIGH" | "MEDIUM" | "LOW";
export type Risk = "LOW" | "MEDIUM" | "HIGH";
export type Priority = "LOW" | "MEDIUM" | "HIGH" | "VERY_HIGH";
export type DtiBand = "SAFE" | "ACCEPTABLE" | "WARNING" | "DANGER";
export type AlertLevel = "INFO" | "WARNING" | "CRITICAL";
export type EfrSafety = "SAFE" | "WARNING" | "CRITICAL";

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
  deadline: string;
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
  savings_planned: number;
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
  overall_health_score: number;
  metric_statuses: Record<string, 'healthy' | 'warning' | 'critical'>;
}

export interface AlertOut {
  code: string;
  level: AlertLevel;
  message: string;
  recommendation: string;
  affected_value: number | null;
}
export interface AlertsOut {
  profile_id: string;
  alerts: AlertOut[];
  has_critical: boolean;
}

export interface GoalImpactOut {
  goal_id: string;
  goal_name: string;
  delay_months: number;
  reachable_by_deadline: boolean;
  monthly_shortfall: number;
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
  efr_safety: EfrSafety;
  delta_pgrs: number;
  total_interest: number;
  flags: string[];
  goal_impacts: GoalImpactOut[];
}
export interface EvaluateIn {
  profile_id: string;
  item_name: string;
  purchase_amount: number;
  candidate_plans: PlanIn[] | null;
}
export interface PlanIn {
  type: "PAY_IN_FULL" | "INSTALLMENT";
  months: number | null;
  apr: number;
}
export interface EvaluateOut {
  best_option_id: string;
  summary: string;
  scorer_used: string;
  balance_recommendation: string;
  options: OptionScoreOut[];
}

export interface ExplainIn {
  profile_id: string;
  item_name: string;
  purchase_amount: number;
  candidate_plans: PlanIn[] | null;
}
export interface ExplanationOut {
  payment_recommendation: string;
  goal_delay_summary: string;
  emergency_fund_assessment: string;
  balanced_option_summary: string;
  source: string;
}

export interface SimulateIn {
  profile_id: string;
  cif?: string;
  purchase_amount: number;
  option_type: "PAY_IN_FULL" | "INSTALLMENT";
  term_months: number | null;
  apr: number;
  horizon_months: number;
  use_forecast: boolean;
}

export interface AdviceOut {
  advice: string;
  scorer_used: string;
}
export interface CashFlowMonthOut {
  month: number;
  year_month: string;
  income_forecast: number;
  expense_forecast: number;
  bnpl_payment: number;
  other_debt_payment: number;
  net_cashflow: number;
  cumulative_balance: number;
  goal_savings: number;
  warning: string;
}
export interface ScenarioSimulationOut {
  option_id: string;
  label: string;
  months: CashFlowMonthOut[];
  total_bnpl_cost: number;
  total_interest: number;
  break_even_month: number | null;
  goal_impact_summary: string;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
}

export interface CifSeed {
  cif: string;
  income: number;
  expense: number;
  debt_payment: number;
}
export interface HistoryPointOut { ds: string; y: number; }
export interface ForecastPointOut { ds: string; yhat: number; lower: number; upper: number; }
export interface ForecastOut {
  cif: string;
  next_30_net: number;
  next_90_net: number;
  history: HistoryPointOut[];
  forecast: ForecastPointOut[];
}
