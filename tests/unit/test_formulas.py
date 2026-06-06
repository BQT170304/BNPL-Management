# tests/unit/test_formulas.py
import pytest

from app.modules.analysis.domain import formulas as f


def test_net_cash_flow():
    assert f.net_cash_flow(14_500_000, 7_800_000, 5_500_000) == 1_200_000


def test_dti():
    assert f.dti(5_500_000, 14_500_000) == pytest.approx(37.93, abs=0.01)


def test_saving_rate():
    ncf = 1_200_000
    assert f.saving_rate(ncf, 0, 14_500_000) == pytest.approx(8.28, abs=0.01)


def test_efr():
    assert f.efr(20_000_000, 6_800_000) == pytest.approx(2.94, abs=0.01)


def test_goal_gap():
    assert f.goal_gap(300_000_000, 0) == 300_000_000


def test_gat():
    assert f.gat(300_000_000, 400_000) == pytest.approx(750.0, abs=0.1)


def test_gat_zero_allocation_is_inf():
    assert f.gat(300_000_000, 0) == float("inf")


def test_goal_delay():
    assert f.goal_delay(750.0, 30) == 720.0


def test_grs_caps_at_100():
    assert f.grs(720.0, 30) == 100.0


def test_grs_zero_when_on_time_or_early():
    assert f.grs(-5.0, 30) == 0.0
    assert f.grs(0.0, 30) == 0.0


def test_grs_overdue_months_remaining_zero_is_100():
    assert f.grs(0.0, 0) == 100.0


def test_pgrs_weighted_average():
    # car GRS100 w3, house GRS100 w4, japan GRS100 w2 -> 100
    assert f.pgrs([(100.0, 3), (100.0, 4), (100.0, 2)]) == pytest.approx(100.0)


def test_pgrs_mixed():
    # (0*3 + 50*1) / 4 = 12.5
    assert f.pgrs([(0.0, 3), (50.0, 1)]) == pytest.approx(12.5)


def test_pgrs_no_goals_is_zero():
    assert f.pgrs([]) == 0.0
