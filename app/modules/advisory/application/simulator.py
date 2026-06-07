from __future__ import annotations

import math
from datetime import date

from app.modules.advisory.domain.options import PaymentOption, PlanType
from app.modules.advisory.domain.simulation import CashFlowMonth, ScenarioSimulation
from app.modules.analysis.domain.results import ProfileMetrics
from app.modules.profiles.domain.entities import FinancialProfile


class BNPLSimulator:
    """Month-by-month cash flow simulation for a single BNPL option.

    Optionally overlays a Prophet forecast (list of (YYYY-MM, net_cashflow) tuples).
    Falls back to flat current-profile figures when no forecast is available.
    """

    def simulate(
        self,
        profile: FinancialProfile,
        metrics: ProfileMetrics,
        option: PaymentOption,
        horizon_months: int = 24,
        monthly_forecast: list[tuple[str, float]] | None = None,
    ) -> ScenarioSimulation:
        base_income = float(profile.total_income)
        base_expense = float(profile.total_expense)
        base_debt = float(profile.total_debt_payment)

        bnpl_months = option.months or 0
        monthly_bnpl = option.monthly_payment

        start = date.today().replace(day=1)
        cumulative = 0.0
        break_even: int | None = None
        months_out: list[CashFlowMonth] = []

        for i in range(horizon_months):
            ym = _add_months(start, i).strftime("%Y-%m")

            if monthly_forecast and i < len(monthly_forecast):
                _, forecasted_ncf = monthly_forecast[i]
                # Derive income so that ncf = forecast - bnpl_pay.
                # Keeping expense realistic: income = forecast + expense + debt
                expense_f = base_expense
                income_f = max(0.0, forecasted_ncf + base_expense + base_debt)
            else:
                income_f = base_income
                expense_f = base_expense

            # BNPL payment only during the financed term (or one-shot at month 0)
            if option.type == PlanType.PAY_IN_FULL:
                bnpl_pay = monthly_bnpl if i == 0 else 0
            else:
                bnpl_pay = monthly_bnpl if i < bnpl_months else 0

            ncf = income_f - expense_f - base_debt - bnpl_pay
            goal_savings = max(0.0, ncf) * 0.4  # rough 40 % of positive NCF to goals
            cumulative += ncf

            if cumulative > 0 and break_even is None and i > 0:
                break_even = i

            warning = ""
            if ncf < 0:
                warning = "NEGATIVE_NCF"
            elif income_f > 0 and ncf / income_f < 0.05:
                warning = "LOW_CASHFLOW"

            months_out.append(CashFlowMonth(
                month=i, year_month=ym,
                income_forecast=income_f, expense_forecast=expense_f,
                bnpl_payment=bnpl_pay, other_debt_payment=int(base_debt),
                net_cashflow=ncf, cumulative_balance=cumulative,
                goal_savings=goal_savings, warning=warning,
            ))

        total_cost = monthly_bnpl * bnpl_months if bnpl_months > 0 else option.upfront
        total_interest = max(0, total_cost - option.upfront)

        neg = sum(1 for m in months_out[:max(bnpl_months, 1)] if m.net_cashflow < 0)
        risk_level = "LOW" if neg == 0 else ("MEDIUM" if neg <= 2 else "HIGH")

        n_goals = len(profile.goals)
        goal_summary = (
            f"Không ảnh hưởng đến {n_goals} mục tiêu" if risk_level == "LOW"
            else f"Có thể trễ kế hoạch {n_goals} mục tiêu ({neg} tháng dòng tiền âm)"
        )

        return ScenarioSimulation(
            option_id=option.id, label=option.label,
            months=months_out, total_bnpl_cost=total_cost,
            total_interest=total_interest, break_even_month=break_even,
            goal_impact_summary=goal_summary, risk_level=risk_level,
        )


def _add_months(d: date, n: int) -> date:
    month = d.month - 1 + n
    year = d.year + month // 12
    month = month % 12 + 1
    return d.replace(year=year, month=month)
