from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date

from app.core.errors import CifNotFound
from app.modules.ingestion.application.ports import (
    CifSummary,
    SummarySource,
    TransactionRow,
    TransactionSource,
)
from app.modules.ingestion.application.services import CifSeed, derive_seed
from app.modules.obligations.domain.entities import (
    Obligation,
    ObligationStatus,
    ObligationType,
)


@dataclass(frozen=True)
class CifObligationSeed:
    source_key: str
    type: ObligationType
    merchant: str
    category: str
    principal_amount: int
    monthly_payment: int
    due_day: int
    start_date: date
    end_date: date
    remaining_terms: int
    apr: float
    status: ObligationStatus
    confidence: float
    evidence_count: int
    active_months: int
    total_paid: int

    def to_obligation(self, profile_id: str) -> Obligation:
        return Obligation(
            id=f"{profile_id}_{self.source_key}",
            profile_id=profile_id,
            type=self.type,
            merchant=self.merchant,
            category=self.category,
            principal_amount=self.principal_amount,
            monthly_payment=self.monthly_payment,
            due_day=self.due_day,
            start_date=self.start_date,
            end_date=self.end_date,
            remaining_terms=self.remaining_terms,
            apr=self.apr,
            status=self.status,
            confidence=self.confidence,
        )


class IngestionService:
    """Loads the summary CSV once and serves CIF lists and derived seeds."""

    def __init__(
        self,
        source: SummarySource,
        csv_path: str,
        transaction_source: TransactionSource | None = None,
        transaction_csv_path: str = "transactions_labeled.csv",
    ) -> None:
        self._source = source
        self._csv_path = csv_path
        self._transaction_source = transaction_source
        self._transaction_csv_path = transaction_csv_path
        self._rows: list[CifSummary] | None = None
        self._transactions: list[TransactionRow] | None = None

    def _summaries(self) -> list[CifSummary]:
        if self._rows is None:
            self._rows = self._source.load(self._csv_path)
        return self._rows

    def _transaction_rows(self) -> list[TransactionRow]:
        if self._transaction_source is None:
            return []
        if self._transactions is None:
            self._transactions = self._transaction_source.load(self._transaction_csv_path)
        return self._transactions

    def list_cifs(self) -> list[str]:
        return sorted({r.cif for r in self._summaries()})

    def summaries_for_cif(self, cif: str) -> list[CifSummary]:
        return [row for row in self._summaries() if row.cif == cif]

    def transactions_for_cif(self, cif: str) -> list[TransactionRow]:
        return [row for row in self._transaction_rows() if row.cif == cif]

    def get_seed(self, cif: str, strategy: str = "latest") -> CifSeed:
        rows = self._summaries()
        if not any(r.cif == cif for r in rows):
            raise CifNotFound(cif)
        return derive_seed(cif, rows, strategy=strategy)

    def get_obligation_seeds(
        self,
        cif: str,
        min_payments: int = 2,
        limit: int = 10,
    ) -> list[CifObligationSeed]:
        if not any(r.cif == cif for r in self._summaries()):
            raise CifNotFound(cif)

        debt_rows = [
            row for row in self._transaction_rows()
            if row.cif == cif and row.category == "Debt payment" and row.amount < 0
        ]
        grouped: dict[str, list[TransactionRow]] = defaultdict(list)
        for row in debt_rows:
            grouped[_normalize_note(row.note)].append(row)

        seeds = [
            _derive_obligation_seed(key, rows)
            for key, rows in grouped.items()
            if len(rows) >= min_payments
        ]
        return sorted(
            seeds,
            key=lambda seed: (seed.monthly_payment, seed.evidence_count),
            reverse=True,
        )[:limit]


def _normalize_note(note: str) -> str:
    text = unicodedata.normalize("NFKD", note)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace("đ", "d").replace("Đ", "d")
    return re.sub(r"\s+", " ", text).strip().lower()


def _source_key(normalized_note: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", normalized_note).strip("_")
    return f"auto_{slug or 'debt'}"


def _obligation_type(normalized_note: str) -> ObligationType:
    if "tra gop" in normalized_note or "tra cham" in normalized_note:
        return ObligationType.BNPL
    if "the" in normalized_note or "tt the" in normalized_note:
        return ObligationType.CREDIT_CARD
    return ObligationType.LOAN


def _derive_obligation_seed(key: str, rows: list[TransactionRow]) -> CifObligationSeed:
    dates = [row.transacted_at.date() for row in rows]
    total_paid = sum(-row.amount for row in rows)
    month_totals: dict[str, int] = defaultdict(int)
    for row in rows:
        month_key = f"{row.transacted_at.year:04d}-{row.transacted_at.month:02d}"
        month_totals[month_key] += -row.amount

    active_months = len(month_totals)
    monthly_payment = total_paid // active_months if active_months else total_paid
    due_day = Counter(d.day for d in dates).most_common(1)[0][0]
    confidence = _confidence(key, rows, month_totals, dates)
    return CifObligationSeed(
        source_key=_source_key(key),
        type=_obligation_type(key),
        merchant=key,
        category="debt",
        principal_amount=total_paid,
        monthly_payment=monthly_payment,
        due_day=due_day,
        start_date=min(dates),
        end_date=max(dates),
        remaining_terms=max(1, active_months),
        apr=0.0,
        status=ObligationStatus.ACTIVE,
        confidence=confidence,
        evidence_count=len(rows),
        active_months=active_months,
        total_paid=total_paid,
    )


def _confidence(
    normalized_note: str,
    rows: list[TransactionRow],
    month_totals: dict[str, int],
    dates: list[date],
) -> float:
    known_keyword = any(
        keyword in normalized_note
        for keyword in ("tra gop", "tra cham", "the", "tt the", "vay", "thau chi", "tra no")
    )
    if not known_keyword:
        return 0.4
    if len(rows) < 3 or len(month_totals) < 3:
        return 0.65
    totals = list(month_totals.values())
    average = sum(totals) / len(totals)
    amount_variation = (
        max(abs(total - average) for total in totals) / average
        if average else 1.0
    )
    day_counts = Counter(d.day for d in dates)
    regular_due_day = day_counts.most_common(1)[0][1] / len(dates) >= 0.35
    if amount_variation <= 0.10 and regular_due_day:
        return 0.9
    return 0.75
