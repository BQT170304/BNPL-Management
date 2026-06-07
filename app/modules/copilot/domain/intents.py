from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum


class CopilotTool(str, Enum):
    RECOMMEND = "RECOMMEND"
    FORECAST = "FORECAST"
    ALERTS = "ALERTS"
    OBLIGATIONS = "OBLIGATIONS"
    EXPLAIN = "EXPLAIN"
    CLARIFY = "CLARIFY"


@dataclass(frozen=True)
class ParsedIntent:
    tool: CopilotTool
    amount: int | None = None
    months: int | None = None
    item_name: str = "Khoản mua"


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return normalized.replace("đ", "d").replace("Đ", "d").lower()


def _parse_amount(norm: str) -> int | None:
    match = re.search(r"(\d[\d.,]*)\s*(trieu|tr)\b", norm)
    if match:
        digits = match.group(1).replace(".", "").replace(",", "")
        if digits.isdigit():
            return int(digits) * 1_000_000
    match = re.search(r"(\d[\d.,]{6,})", norm)
    if match:
        digits = match.group(1).replace(".", "").replace(",", "")
        if digits.isdigit():
            return int(digits)
    return None


def _parse_months(norm: str) -> int | None:
    match = re.search(r"(\d+)\s*thang", norm)
    return int(match.group(1)) if match else None


def _parse_item(norm: str) -> str:
    match = re.search(r"mua\s+([a-z ]+?)\s+(?:gia|\d|tra)", norm)
    if match:
        item = match.group(1).strip()
        if item:
            return item
    return "Khoản mua"


def parse_intent(message: str) -> ParsedIntent:
    """Deterministic intent router. No LLM is used to decide the tool."""

    norm = _normalize(message)
    amount = _parse_amount(norm)
    months = _parse_months(norm)
    item = _parse_item(norm)

    if any(k in norm for k in ("giai thich", "tai sao", "vi sao", "ly do")):
        tool = CopilotTool.EXPLAIN
    elif any(k in norm for k in ("nen mua", "co nen", "tra gop", "tra cham")) or amount:
        tool = CopilotTool.RECOMMEND
    elif any(k in norm for k in ("du bao", "dong tien", "thang toi")):
        tool = CopilotTool.FORECAST
    elif any(k in norm for k in ("canh bao", "rui ro")):
        tool = CopilotTool.ALERTS
    elif any(k in norm for k in ("nghia vu", "khoan no", "dang no")):
        tool = CopilotTool.OBLIGATIONS
    else:
        tool = CopilotTool.CLARIFY

    return ParsedIntent(tool=tool, amount=amount, months=months, item_name=item)
