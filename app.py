"""Streamlit presentation only; financial calculations belong to the backend."""

from datetime import date
from html import escape
import inspect
import math
import re

import streamlit as st

import data_loader
import portfolio_math


st.set_page_config(
    page_title="Portfolio Risk Optimizer", page_icon="◈", layout="wide"
)

PERIODS = {"1 year": 1, "3 years": 3, "5 years": 5}
DEFAULT_TICKERS = ("SPY", "GLD")
ASSET_COLORS = ("#63d8bd", "#94a9ff")


class BackendIntegrationError(Exception):
    """An existing backend function cannot fulfill the requested UI action."""


@st.cache_data(ttl=3600, max_entries=64, show_spinner=False)
def load_asset_returns(ticker: str, start: date, end: date):
    """Cache the existing loader's output without changing its calculations."""
    return data_loader.get_return(ticker, start, end)


def validate_tickers(raw_tickers):
    tickers = tuple(value.strip().upper() for value in raw_tickers)
    for index, ticker in enumerate(tickers, start=1):
        if not ticker:
            raise ValueError(f"Enter a ticker symbol for asset {index}.")
        if not re.fullmatch(r"[A-Z0-9^][A-Z0-9.^=\-]{0,19}", ticker):
            raise ValueError(
                f"Asset {index} needs a valid ticker symbol, such as SPY, GLD, or BRK-B."
            )
    if len(set(tickers)) != len(tickers):
        raise ValueError("Choose two different ticker symbols to compare their allocation.")
    return tickers


def run_backend_optimizer(returns, tickers):
    """Call the backend optimizer; never calculate an alternative optimum."""
    optimizer = portfolio_math.min_volatility_weight
    # Accept the current one-argument API and the suggested ticker-aware API.
    try:
        inspect.signature(optimizer).bind(returns, *tickers)
    except TypeError:
        args = (returns,)
    else:
        args = (returns, *tickers)
    try:
        weight, volatility = optimizer(*args)
    except TypeError as exc:
        raise BackendIntegrationError(
            "The backend optimizer could not run. Its current calls to "
            "portfolio_volatility omit the ticker arguments. See FRONTEND.md "
            "for the suggested backend changes; no allocation was calculated."
        ) from exc
    weight, volatility = float(weight), float(volatility)
    if not math.isfinite(weight) or not 0 <= weight <= 1:
        raise BackendIntegrationError("The backend returned an invalid allocation.")
    if not math.isfinite(volatility) or volatility < 0:
        raise BackendIntegrationError("The backend returned an invalid volatility.")
    return weight, volatility


def render_allocation(tickers, weight):
    percentages = (weight * 100, (1 - weight) * 100)
    labels = [f"{ticker}: {pct:.1f}%" for ticker, pct in zip(tickers, percentages)]
    segments = "".join(
        f'<span style="width:{pct:.6f}%;background:{color}"></span>'
        for pct, color in zip(percentages, ASSET_COLORS)
    )
    st.markdown(
        f'<div class="allocation-bar" role="img" '
        f'aria-label="{escape(", ".join(labels), quote=True)}">{segments}</div>',
        unsafe_allow_html=True,
    )
    columns = st.columns(len(tickers))
    for column, label, color in zip(columns, labels, ASSET_COLORS):
        with column:
            st.markdown(
                f'<div class="allocation-label"><span style="color:{color}">●</span> '
                f'{escape(label)}</div>', unsafe_allow_html=True
            )


def render_risk_chart(result):
    # analysis.py currently executes on import and cannot be safely imported.
    # Activate this hook only after the backend owner exposes a plot function
    # and a main guard. No Matplotlib plot is recreated in the frontend.
    st.info(
        "The risk graph is unavailable until analysis.py exposes its existing "
        "plot as an import-safe function returning a Matplotlib Figure. "
        "The integration example is in FRONTEND.md."
    )


def main():
    st.markdown(
        """
        <style>
        .stApp { background: #0c111b; }
        .block-container { max-width: 1180px; padding-top: 3rem; padding-bottom: 3rem; }
        h1 { letter-spacing: -0.045em; }
        h2, h3 { letter-spacing: -0.025em; }
        [data-testid="stMetric"] { padding: 1.25rem; border: 1px solid #273245;
            border-radius: 14px; background: #141c2a; }
        [data-testid="stMetricLabel"] { color: #a8b4c9; }
        [data-testid="stMetricValue"] { letter-spacing: -0.035em; }
        [data-testid="stForm"] { background: #111927; border-color: #273245; }
        .eyebrow { color: #63d8bd; font-size: .75rem; font-weight: 650;
            letter-spacing: .15em; margin-bottom: .6rem; }
        .intro { color: #a8b4c9; font-size: 1.1rem; margin-bottom: 2rem; }
        .allocation-bar { height: 24px; display: flex; overflow: hidden;
            border-radius: 8px; background: #273245; margin: 1rem 0; }
        .allocation-label { color: #dbe4f3; font-size: .9rem; }
        .empty-state { padding: 1.8rem 1rem; text-align: center; }
        .empty-icon { font-size: 2.2rem; color: #63d8bd; margin-bottom: .5rem; }
        .empty-title { color: #e8eef8; font-size: 1.15rem; font-weight: 600; }
        .empty-copy { color: #a8b4c9; max-width: 440px; margin: .5rem auto; }
        </style>
        """, unsafe_allow_html=True,
    )
    st.markdown('<div class="eyebrow">PORTFOLIO RESEARCH / TWO ASSETS</div>', unsafe_allow_html=True)
    st.title("Portfolio Risk Optimizer")
    st.markdown(
        '<div class="intro">Find the minimum-volatility allocation for your investments.</div>',
        unsafe_allow_html=True,
    )

    configuration, workspace = st.columns([1, 2.2], gap="large")
    with configuration:
        with st.form("portfolio_configuration"):
            st.subheader("Portfolio configuration")
            st.caption("Choose your assets and historical window.")
            raw_tickers = [
                st.text_input(f"Asset {index + 1} ticker", value=ticker,
                              max_chars=20, key=f"ticker_{index}")
                for index, ticker in enumerate(DEFAULT_TICKERS)
            ]
            period = st.selectbox("Historical period", list(PERIODS), index=1)
            submitted = st.form_submit_button(
                "Optimize Portfolio", type="primary", use_container_width=True
            )
        st.caption("Daily returns · historical data · long-only allocation")
        with st.expander("Backend connection"):
            st.write("Market data and risk calculations use your existing Python modules.")
            st.warning("The optimizer and graph currently need backend integration changes.")
            st.caption("Backend files have been left unchanged. See FRONTEND.md.")

    if submitted:
        # Clear old results before every attempt so an error cannot show stale allocations.
        st.session_state.pop("optimization_result", None)
        st.session_state.pop("optimization_error", None)
        try:
            tickers = validate_tickers(raw_tickers)
            end = date.today()
            try:
                start = end.replace(year=end.year - PERIODS[period])
            except ValueError:
                start = end.replace(year=end.year - PERIODS[period], day=28)
            with st.spinner("Loading historical returns and calling your optimizer…"):
                asset_returns = [load_asset_returns(ticker, start, end) for ticker in tickers]
                returns = data_loader.combine_df(*asset_returns)
                if len(returns) < 2:
                    raise ValueError("Not enough overlapping daily returns. Try another period or pair.")
                if not all(ticker in returns.columns for ticker in tickers):
                    raise BackendIntegrationError("The data loader did not return both ticker columns.")
                if not all(math.isfinite(float(value)) for value in returns.to_numpy().ravel()):
                    raise ValueError("The retrieved returns contain non-finite values. Try another pair.")
                weight, volatility = run_backend_optimizer(returns, tickers)
                st.session_state.optimization_result = {
                    "tickers": tickers, "weight": weight, "volatility": volatility,
                    "period": period, "start": start, "end": end, "returns": returns,
                }
        except (ValueError, BackendIntegrationError) as exc:
            st.session_state.optimization_error = str(exc)
        except Exception:
            st.session_state.optimization_error = (
                "Market data or the backend calculation could not be completed. "
                "Check the ticker symbols and connection, then try again."
            )

    with workspace:
        result = st.session_state.get("optimization_result")
        error = st.session_state.get("optimization_error")
        if error:
            st.error(error)
        with st.container(border=True):
            st.subheader("Optimization results")
            if result is None:
                st.markdown(
                    '<div class="empty-state"><div class="empty-icon">◈</div>'
                    '<div class="empty-title">Your allocation starts here</div>'
                    '<div class="empty-copy">Choose two assets and optimize to request '
                    'an allocation from your Python backend.</div></div>',
                    unsafe_allow_html=True,
                )
                st.caption("No allocation or volatility result is available yet.")
            else:
                tickers = result["tickers"]
                st.caption(
                    f'{" + ".join(tickers)} · {result["period"]} · '
                    f'{result["start"]:%d %b %Y} – {result["end"]:%d %b %Y} (end exclusive)'
                )
                cards = st.columns(3)
                cards[0].metric(f"{tickers[0]} allocation", f'{result["weight"]:.1%}')
                cards[1].metric(f"{tickers[1]} allocation", f'{1 - result["weight"]:.1%}')
                cards[2].metric("Annualized volatility", f'{result["volatility"]:.2%}')
                render_allocation(tickers, result["weight"])
                st.caption(f'{len(result["returns"]):,} overlapping daily returns · Results from the backend optimizer')

        with st.container(border=True):
            st.subheader("Risk visualization")
            st.caption("Portfolio volatility versus asset allocation")
            render_risk_chart(result)

    st.divider()
    st.caption("PORTFOLIO RISK OPTIMIZER · Data: Yahoo Finance via your existing yfinance loader")


if __name__ == "__main__":
    main()
