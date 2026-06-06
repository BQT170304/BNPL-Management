# tests/unit/test_money.py
import pytest

from app.core.money import format_vnd, percent, ratio, share_split


def test_percent_basic():
    assert percent(5_500_000, 14_500_000) == pytest.approx(37.93, abs=0.01)


def test_percent_zero_denominator_returns_inf():
    assert percent(1, 0) == float("inf")


def test_percent_zero_over_zero_is_zero():
    assert percent(0, 0) == 0.0


def test_ratio_basic():
    assert ratio(20_000_000, 7_800_000) == pytest.approx(2.564, abs=0.001)


def test_format_vnd():
    assert format_vnd(14_500_000) == "14.500.000 ₫"


def test_share_split_even():
    # split 1_200_000 into 3 equal integer shares, remainder to first
    assert share_split(1_200_000, [1, 1, 1]) == [400_000, 400_000, 400_000]


def test_share_split_weighted_conserves_total():
    parts = share_split(1_000_000, [4, 3, 2])
    assert sum(parts) == 1_000_000
    assert parts[0] > parts[1] > parts[2]
