"""Extract a financial profile from raw transaction rows.

Expected columns: CIF_NO, NOTE, TRAN_DATE, AMOUNT
- NOTE: free Vietnamese text (no diacritics)
- AMOUNT: positive = credit/income, negative = debit/expense
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Sequence


# ── keyword banks ──────────────────────────────────────────────────────────────

_INC_SALARY = [
    "luong", "ung luong", "chi tra luong", "tra luong", "nhan luong",
    "phu cap", "tro cap", "phu cap an", "phu cap di lai",
    "thu lao", "tien cong", "tien thuong", "thuong", "thuong quy",
    "thu nhap", "tien sinh hoat", "bao nuoi", "gia dinh gui tien",
]
_INC_BONUS = ["thuong", "bonus", "thuong du an", "thuong kpi", "thuong tet", "thuong quy"]
_INC_PASSIVE = ["lai suat", "lai tiet kiem", "thu nhap thu dong", "cho thue"]
_INC_SECONDARY = ["thu lao freelance", "thu lao cong tac", "thu lao bien tap",
                  "cong tac phi", "thu nhap them", "thu nhap phu", "lam them",
                  "part time", "lam part"]

_HOUSING = ["tien nha", "tien phong", "nha tro", "phong tro", "thue nha",
            "phi quan ly", "phi dich vu", "toa nha", "chung cu", "can ho", "phi nha"]
_UTILITIES = ["tien dien", "dien nang", "tien nuoc", "nuoc sinh hoat",
              "tien mang", "internet", "wifi", "cap quang", "vien thong", "tien gas"]
_FOOD = ["an trua", "an sang", "an toi", "do an", "tien an", "tien com", "com binh",
         "bun bo", "bun rieu", "pho", "com rang", "banh mi", "cafe", "tra sua",
         "nuoc ngot", "nuoc ep", "bua an", "share tien an", "an lau", "an nhau",
         "lien hoan", "buffet", "an vat", "sieu thi thuc pham", "rap chieu phim"]
_TRANSPORT = ["do xang", "xang xe", "xe om", "grab", "taxi", "be car",
              "gofood", "baemin", "ve tau", "ve xe buyt", "phi gui xe",
              "phi bai xe", "phi duong bo", "gviet", "go viet", "bus"]
_DEBT = ["tra gop", "gop thang", "tra no", "tra no thau chi", "tra no the",
         "thanh toan the", "tt the", "thanh toan the tin dung", "tra the",
         "dang ky tra gop", "tra vay", "tien vay", "du no", "tat no", "thau chi"]
_HEALTH = ["thuoc", "benh vien", "kham benh", "phong kham", "y te",
           "vien phi", "toa thuoc", "kham pha", "nha khoa"]
_EDUCATION = ["hoc phi", "hoc them", "tien hoc", "truong", "hoc lai",
              "khoa hoc", "sach giao khoa", "lop hoc", "dao tao"]
_ENTERTAIN = ["phim", "karaoke", "du lich", "nghi duong", "giai tri", "game",
              "the gym", "spa", "massage", "thu gian", "dich vu giai tri"]
_SHOPPING = ["mua do", "mua hang", "ck don hang", "chot don", "mua online",
             "lazada", "shopee", "tiki", "dat hang", "phi ship", "mua sam"]


def _match(note: str, keywords: list[str]) -> bool:
    return any(kw in note for kw in keywords)


@dataclass
class RawTransaction:
    note: str
    tran_date: datetime
    amount: float

    @property
    def month_key(self) -> str:
        return self.tran_date.strftime("%Y-%m")


@dataclass
class ExtractedProfile:
    salary: int
    secondary: int
    avg_bonus_monthly: int
    passive: int
    monthly_housing: int
    monthly_utilities: int
    monthly_food: int
    monthly_transport: int
    monthly_health: int
    monthly_education: int
    monthly_entertainment: int
    monthly_shopping: int
    monthly_other_expense: int
    monthly_debt_payment: int
    months_analyzed: int
    cif: str = ""


# ── public API ─────────────────────────────────────────────────────────────────

def extract_from_bytes(file_bytes: bytes, filename: str) -> tuple[ExtractedProfile, list[RawTransaction]]:
    """Parse uploaded CSV/XLSX bytes and extract a financial profile."""
    import pandas as pd

    if filename.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(file_bytes))
        # Handle "CSV packed in Excel" format (single column)
        if df.shape[1] == 1:
            from io import StringIO
            csv_text = "\n".join(df.iloc[:, 0].dropna().astype(str).tolist())
            df = pd.read_csv(StringIO("CIF_NO,NOTE,TRAN_DATE,AMOUNT\n" + csv_text))
    else:
        df = pd.read_csv(io.BytesIO(file_bytes))

    df.columns = [c.strip().upper() for c in df.columns]
    required = {"NOTE", "TRAN_DATE", "AMOUNT"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"File thiếu cột: {', '.join(missing)}")

    df["NOTE"] = df["NOTE"].fillna("").astype(str).str.strip().str.lower()
    df["AMOUNT"] = pd.to_numeric(df["AMOUNT"], errors="coerce").fillna(0).astype(float)
    df["TRAN_DATE"] = pd.to_datetime(df["TRAN_DATE"], errors="coerce")
    df = df.dropna(subset=["TRAN_DATE"])

    # Deduplication (simulation data has many exact duplicates)
    df = df.drop_duplicates(subset=["NOTE", "TRAN_DATE", "AMOUNT"])

    cif = str(df["CIF_NO"].iloc[0]) if "CIF_NO" in df.columns else ""

    txns = [
        RawTransaction(note=row["NOTE"], tran_date=row["TRAN_DATE"], amount=float(row["AMOUNT"]))
        for _, row in df.iterrows()
    ]

    return extract_profile(txns, cif=cif), txns


def extract_profile(txns: Sequence[RawTransaction], cif: str = "") -> ExtractedProfile:
    """Categorize transactions and average over complete months."""
    if not txns:
        raise ValueError("Không có giao dịch hợp lệ trong file")

    # Group by month
    months: dict[str, list[RawTransaction]] = {}
    for t in txns:
        months.setdefault(t.month_key, []).append(t)

    # Keep only months with ≥10 transactions (skip partial edge months)
    complete = {k: v for k, v in months.items() if len(v) >= 5}
    if not complete:
        complete = months  # fallback: use all

    n_months = max(len(complete), 1)

    # Accumulators
    salary_total = secondary_total = bonus_total = passive_total = 0.0
    housing = utilities = food = transport = health = education = 0.0
    entertainment = shopping = debt = other_expense = 0.0

    for _, month_txns in complete.items():
        for t in month_txns:
            note, amt = t.note, t.amount

            if amt > 0:
                if _match(note, _INC_BONUS):
                    bonus_total += amt
                elif _match(note, _INC_PASSIVE):
                    passive_total += amt
                elif _match(note, _INC_SECONDARY):
                    secondary_total += amt
                elif _match(note, _INC_SALARY):
                    salary_total += amt
                # Other positive (transfers received) counted as secondary
                else:
                    secondary_total += amt * 0.3  # conservative — not all transfers are income
            else:
                a = abs(amt)
                if _match(note, _DEBT):
                    debt += a
                elif _match(note, _HOUSING):
                    housing += a
                elif _match(note, _UTILITIES):
                    utilities += a
                elif _match(note, _FOOD):
                    food += a
                elif _match(note, _TRANSPORT):
                    transport += a
                elif _match(note, _HEALTH):
                    health += a
                elif _match(note, _EDUCATION):
                    education += a
                elif _match(note, _ENTERTAIN):
                    entertainment += a
                elif _match(note, _SHOPPING):
                    shopping += a
                else:
                    other_expense += a

    def _avg(v: float) -> int:
        return round(v / n_months)

    salary_avg = _avg(salary_total)
    secondary_avg = _avg(secondary_total)
    bonus_monthly = _avg(bonus_total / 3)  # bonuses are typically quarterly
    passive_avg = _avg(passive_total)

    return ExtractedProfile(
        cif=cif,
        salary=salary_avg,
        secondary=secondary_avg,
        avg_bonus_monthly=bonus_monthly,
        passive=passive_avg,
        monthly_housing=_avg(housing),
        monthly_utilities=_avg(utilities),
        monthly_food=_avg(food),
        monthly_transport=_avg(transport),
        monthly_health=_avg(health),
        monthly_education=_avg(education),
        monthly_entertainment=_avg(entertainment),
        monthly_shopping=_avg(shopping),
        monthly_other_expense=_avg(other_expense),
        monthly_debt_payment=_avg(debt),
        months_analyzed=n_months,
    )
