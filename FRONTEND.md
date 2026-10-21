# Streamlit frontend

The dashboard is implemented in `app.py`. `.streamlit/config.toml` supplies the
dark theme; `requirements-ui.txt` contains only the new frontend dependency.
No existing backend file has been changed.

## Launch

From this project directory, use the existing environment:

```sh
source venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

If setting up a fresh environment, also install the existing backend's
dependencies: `python -m pip install pandas numpy yfinance matplotlib`.

## Integration and behavior

- `data_loader.get_return(ticker, start, end)` supplies daily returns. The UI
  caches individual calls for one hour, keyed by ticker and exact dates, with
  at most 64 entries. Errors are not cached. Calculations are not cached.
- `data_loader.combine_df(df1, df2)` aligns and cleans the two return series.
- `portfolio_math.min_volatility_weight(...)` is the sole source of an optimum.
  The UI accepts its existing single-argument signature or the suggested
  ticker-aware signature below. It checks that returned values are valid but
  does not implement any optimization algorithm.
- `portfolio_math.portfolio_volatility` is not reimplemented or monkeypatched.
  Its existing annualization uses 252 trading days.
- `analysis.py` is intentionally not imported: it downloads data and runs
  `plt.show()` immediately on import. No callable plotting function exists yet.

Submitting the form loads real data and calls the optimizer. With the current
backend, the optimizer raises `TypeError`; the dashboard displays a helpful
message instead of inventing an allocation. Data retrieval errors and insufficient
overlapping observations also produce messages. Every submission clears previous
results so failures never leave stale allocations on screen. Successful results
remain in session state until the next submission; editing an unsubmitted form
does not change their ticker/date labels.

Dates are calendar-year lookbacks ending today (the loader treats the end date
as exclusive). A February 29 start falls back to February 28 in a non-leap year.
Daily coverage depends on the assets' available history. The ticker list and
allocation renderer are iterable, but the backend adapter remains explicitly
two-asset until the backend supports more assets.

## Suggested backend changes — examples only, not applied

### 1. Repair the optimizer's argument mismatch and accept ticker symbols

`portfolio_volatility(returns, ticker1, ticker2, w)` requires four arguments,
but `min_volatility_weight` currently passes only two. It fails before examining
the allocation grid. Pass both symbols through while retaining your existing
grid search and formulas. The frontend automatically recognizes this signature:

```python
# Suggested change in portfolio_math.py; apply this yourself if desired.
def min_volatility_weight(returns, ticker1, ticker2):
    min_volatility_w = 0.0
    annual_min_volatility = portfolio_volatility(returns, ticker1, ticker2, 0)
    for i in range(101):
        w = i / 100
        vol = portfolio_volatility(returns, ticker1, ticker2, w)
        if vol < annual_min_volatility:
            min_volatility_w = w
            annual_min_volatility = vol
    return min_volatility_w, annual_min_volatility
```

The direct-execution example in that module would then need
`min_volatility_weight(fake, "SPY", "GLD")`. This remains a minimum on your
existing 1-percentage-point grid, rather than a continuous optimum.

### 2. Make the existing analysis graph import-safe and return its Figure

`analysis.py` also calls `get_return` without the required `start` and `end`
arguments. Put executable downloads under `if __name__ == "__main__":`, pass
those dates, and expose the existing graph as a callable. The following shows
how you could move the current loop and plot into a function. The explicit
minimum marker and legend are additions you would implement in the backend:

```python
# Suggested function in analysis.py; apply this yourself if desired.
def plot_portfolio_risk(returns, ticker1, ticker2, best_weight, best_volatility):
    arr = np.array([])
    weights = np.array([])
    for i in range(101):
        w = i / 100
        arr = np.append(
            arr, portfolio_math.portfolio_volatility(returns, ticker1, ticker2, w)
        )
        weights = np.append(weights, w)

    fig, ax = plt.subplots()
    ax.plot(weights, arr, label="Annualized portfolio volatility")
    ax.scatter([best_weight], [best_volatility], label="Minimum volatility", zorder=3)
    ax.set_xlabel(f"{ticker1} Weight")
    ax.set_ylabel("Annualized Portfolio Volatility")
    ax.set_title(f"Portfolio Volatility vs {ticker1} Weight")
    ax.grid(True)
    ax.legend()
    return fig
```

Keep `plt.show()` only in your guarded command-line example, outside this
function. Once you have made `analysis.py` safe to import, replace the placeholder
inside the **frontend** `render_risk_chart` function with this integration:

```python
if result is None:
    st.info("Optimize a portfolio to view its risk curve.")
    return

from analysis import plot_portfolio_risk
import matplotlib.pyplot as plt

fig = plot_portfolio_risk(
    result["returns"], *result["tickers"], result["weight"], result["volatility"]
)
try:
    st.pyplot(fig)
finally:
    plt.close(fig)
```

Until that hook exists, the dashboard displays an unavailable-graph message.
No risk plot is recreated by frontend code.

### 3. Optional backend validation

Consider having your backend reject too-short, non-finite, or missing-column
return data itself, so non-UI callers get the same protection. The frontend
already checks these cases before invoking the optimizer; no backend processing
has been changed. Add these checks yourself if useful.

## Frontend verification

```sh
venv/bin/python -m unittest discover -s tests -p 'test_frontend.py'
```

The tests use Streamlit's `AppTest` and isolated market-data/optimizer test
doubles. They check form validation, the real optimizer's integration error,
unavailable and invalid data, cache reuse, backend result presentation, and
clearing stale results. Test values never appear in the deployed application.
These are offline UI checks, not verification of live Yahoo Finance availability
or of the backend's financial formulas.

Streamlit references: [AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest)
and [API reference](https://docs.streamlit.io/develop/api-reference).
