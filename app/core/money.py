# app/core/money.py
"""Money helpers. Currency is always int VNĐ; never use float for money."""
from __future__ import annotations

Money = int


def percent(numerator: float, denominator: float) -> float:
    """numerator / denominator as a percentage. 0/0 -> 0; x/0 (x!=0) -> inf."""
    if denominator == 0:
        return 0.0 if numerator == 0 else float("inf")
    return numerator / denominator * 100.0


def ratio(numerator: float, denominator: float) -> float:
    """numerator / denominator as a plain ratio. 0/0 -> 0; x/0 -> inf."""
    if denominator == 0:
        return 0.0 if numerator == 0 else float("inf")
    return numerator / denominator


def format_vnd(amount: Money) -> str:
    """Format an int VNĐ with dot thousands separators, e.g. '14.500.000 ₫'."""
    return f"{amount:,.0f}".replace(",", ".") + " ₫"


def share_split(total: Money, weights: list[int]) -> list[Money]:
    """Split an integer total into shares proportional to weights.

    Uses largest-remainder so the shares sum exactly to total. Empty weights -> [].
    """
    if not weights:
        return []
    weight_sum = sum(weights)
    if weight_sum == 0:
        return [0 for _ in weights]
    raw = [total * w / weight_sum for w in weights]
    floored = [int(x) for x in raw]
    remainder = total - sum(floored)
    # distribute the leftover units to the largest fractional remainders
    order = sorted(range(len(weights)), key=lambda i: raw[i] - floored[i], reverse=True)
    for i in range(remainder):
        floored[order[i % len(order)]] += 1
    return floored
