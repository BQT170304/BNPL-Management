# tests/unit/test_thresholds.py
from app.modules.analysis.domain.thresholds import DtiBand, classify_dti


def test_dti_bands():
    assert classify_dti(15) == DtiBand.SAFE
    assert classify_dti(25) == DtiBand.ACCEPTABLE
    assert classify_dti(37.93) == DtiBand.WARNING
    assert classify_dti(45) == DtiBand.DANGER


def test_dti_band_boundaries_lower_inclusive():
    assert classify_dti(20) == DtiBand.ACCEPTABLE
    assert classify_dti(35) == DtiBand.WARNING
    assert classify_dti(40) == DtiBand.DANGER
