from __future__ import annotations

import pandas as pd

from app.modules.ingestion.application.ports import TransactionRow


class CsvTransactionSource:
    def load(self, path: str) -> list[TransactionRow]:
        df = pd.read_csv(path, dtype={"CIF_NO": str})
        df["TRAN_DATE"] = pd.to_datetime(df["TRAN_DATE"], errors="coerce")
        rows: list[TransactionRow] = []
        for _, row in df.dropna(subset=["TRAN_DATE"]).iterrows():
            rows.append(TransactionRow(
                cif=str(row["CIF_NO"]),
                note=str(row["NOTE"]),
                transacted_at=row["TRAN_DATE"].to_pydatetime(),
                amount=int(row["AMOUNT"]),
                category=str(row["CATEGORY"]),
            ))
        return rows
