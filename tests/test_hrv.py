import numpy as np

from src.hrv import pnn50, rmssd, sdnn


def test_rmssd_flat_rr_is_zero():
    assert rmssd(np.array([800.0, 800.0, 800.0, 800.0])) == 0.0


def test_sdnn_and_pnn50_sanity():
    rr = np.array([800.0, 850.0, 790.0, 860.0, 800.0])
    assert sdnn(rr) > 0
    assert 0 <= pnn50(rr) <= 100
