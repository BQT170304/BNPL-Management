from __future__ import annotations

import pandas as pd

from app.modules.ingestion.application.ports import CifSummary


class CsvSummarySource:
    def load(self, path: str) -> list[CifSummary]:
        df = pd.read_csv(path, dtype={"CIF_NO": str})
        return [
            CifSummary(
                cif=row["CIF_NO"], month=row["MONTH"],
                income=int(row["total_income"]),
                expense=int(row["total_expense"]),
                debt_payment=int(row["total_debt_payment"]),
            )
            for _, row in df.iterrows()
        ]
