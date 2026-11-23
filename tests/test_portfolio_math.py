import numpy as np
import pandas as pd
import pytest

from portfolio_math import min_volatility_weight, portfolio_volatility


def make_returns(n=5000, sigma1=0.01, sigma2=0.01, rho=0.0, seed=0):
    rng = np.random.default_rng(seed)
    cov = [[sigma1**2, rho * sigma1 * sigma2], [rho * sigma1 * sigma2, sigma2**2]]
    data = rng.multivariate_normal([0, 0], cov, size=n)
    return pd.DataFrame(data, columns=["A", "B"])


def test_all_in_one_asset_gives_its_own_volatility():
    r = make_returns()
    assert portfolio_volatility(r, "A", "B", 1) == pytest.approx(r["A"].std() * np.sqrt(252))
    assert portfolio_volatility(r, "A", "B", 0) == pytest.approx(r["B"].std() * np.sqrt(252))


def test_equal_volatility_uncorrelated_assets_split_50_50():
    r = make_returns(rho=0.0)
    w, _ = min_volatility_weight(r, "A", "B")
    assert w == pytest.approx(0.5, abs=0.03)


def test_matches_closed_form_minimum():
    # w* = (s2^2 - cov) / (s1^2 + s2^2 - 2 cov)
    r = make_returns(sigma1=0.01, sigma2=0.02, rho=0.3)
    s1, s2, c = r["A"].var(), r["B"].var(), r["A"].cov(r["B"])
    w_exact = (s2 - c) / (s1 + s2 - 2 * c)
    w, _ = min_volatility_weight(r, "A", "B")
    assert w == pytest.approx(w_exact, abs=0.01)


def test_diversification_lowers_volatility():
    r = make_returns(rho=0.0)
    _, vol = min_volatility_weight(r, "A", "B")
    assert vol < portfolio_volatility(r, "A", "B", 1)
    assert vol < portfolio_volatility(r, "A", "B", 0)


def test_weight_outside_0_1_raises():
    r = make_returns(n=10)
    with pytest.raises(ValueError):
        portfolio_volatility(r, "A", "B", 1.5)
