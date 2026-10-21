import numpy as np
import pandas as pd


def portfolio_volatility(returns, ticker1, ticker2, w):
    """Annualised volatility of a portfolio with weight w in SPY and 1 - w in GLD."""
    if not 0 <= w <= 1:
        raise ValueError(f"w must be between 0 and 1, got {w}")
    var_spy = returns[f"{ticker1}"].var()
    var_gld = returns[f"{ticker2}"].var()
    cov_sg = returns[f"{ticker1}"].cov(returns[f"{ticker2}"])
    var_portfolio = w ** 2 * var_spy + (1 - w) ** 2 * var_gld + 2 * w * (1 - w) * cov_sg 
    daily_volatility = np.sqrt(var_portfolio)
    annual_volatility = daily_volatility * np.sqrt(252)
    return annual_volatility

def min_volatility_weight(returns, ticker1, ticker2):
    """Return (weight in ticker1, annualised volatility) of the minimum-volatility portfolio."""
    min_volatility_w = 0.0
    annual_min_volatility = portfolio_volatility(returns, ticker1, ticker2, 0)
    for i in range(101):
        w = i / 100
        vol = portfolio_volatility(returns, ticker1, ticker2, w)
        if vol < annual_min_volatility:
            min_volatility_w = w
            annual_min_volatility = vol
    return min_volatility_w, annual_min_volatility

if __name__ == "__main__":
    fake = pd.DataFrame({
        "SPY": [0.01, -0.02, 0.015, 0.005],
        "GLD": [-0.005, 0.01, 0.0, 0.002],
    })
    best_w, best_vol = min_volatility_weight(fake, "SPY", "GLD")
    print(best_w, best_vol)





    



