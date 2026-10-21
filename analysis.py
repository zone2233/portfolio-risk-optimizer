import matplotlib.pyplot as plt
import data_loader
import portfolio_math
from matplotlib.ticker import PercentFormatter 

def plot_portfolio_risk(returns, ticker1, ticker2, best_weight, best_volatility):
    """Return a Figure of annualised volatility against the weight in ticker1."""
    weights, vols = portfolio_math.volatility_curve(returns, ticker1, ticker2)

    fig, ax = plt.subplots()
    ax.plot(weights, vols, label="Annualised volatility")
    ax.scatter(
        [best_weight], [best_volatility],
        color="red", zorder=3, label="Minimum volatility",
    )
    ax.set_xlabel(f"Weight in {ticker1} (rest in {ticker2})")
    ax.set_ylabel("Annualised volatility")
    ax.set_title(f"Portfolio volatility: {ticker1} / {ticker2}")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.grid(True)
    ax.legend()
    return fig

def main(ticker1="SPY", ticker2="GLD", start="2025-01-01", end="2026-01-01"):
    """Load returns, find the minimum-volatility weight, then print, save and show the chart."""
    returns1 = data_loader.get_return(ticker1, start, end)
    returns2 = data_loader.get_return(ticker2, start, end)
    returns = data_loader.combine_df(returns1, returns2)
    best_w, best_vol = portfolio_math.min_volatility_weight(returns, ticker1, ticker2)
    print(f"Minimum volatility: {best_w:.0%} {ticker1} / {1 - best_w:.0%} {ticker2}, "
      f"annualised volatility {best_vol:.2%}")
    fig = plot_portfolio_risk(returns, ticker1, ticker2, best_w, best_vol);
    fig.savefig("risk_curve.png", dpi=150, bbox_inches="tight");
    plt.show()

if __name__ == "__main__":
    main()

