"""Streamlit app: minimum-volatility allocation between two assets."""

from datetime import date

import matplotlib.pyplot as plt
import streamlit as st

import data_loader
import portfolio_math
from analysis import plot_portfolio_risk

PERIODS = {"1 year": 1, "3 years": 3, "5 years": 5}


@st.cache_data(ttl=3600)
def load_returns(ticker1, ticker2, start, end):
    r1 = data_loader.get_return(ticker1, start, end)
    r2 = data_loader.get_return(ticker2, start, end)
    return data_loader.combine_df(r1, r2)


st.title("Portfolio Risk Optimizer")
st.write(
    "Finds the long-only allocation between two assets with the lowest "
    "historical volatility, using daily returns from Yahoo Finance."
)

with st.sidebar:
    ticker1 = st.text_input("Asset 1", "SPY").strip().upper()
    ticker2 = st.text_input("Asset 2", "GLD").strip().upper()
    period = st.selectbox("Estimation window", list(PERIODS))
    run = st.button("Optimise")

if run:
    if not ticker1 or not ticker2 or ticker1 == ticker2:
        st.error("Enter two different tickers.")
        st.stop()

    end = date.today()
    start = date(end.year - PERIODS[period], end.month, min(end.day, 28))

    try:
        returns = load_returns(ticker1, ticker2, start, end)
    except ValueError as e:
        st.error(str(e))
        st.stop()

    if len(returns) < 30:
        st.error("Not enough overlapping data for these two tickers.")
        st.stop()

    w, vol = portfolio_math.min_volatility_weight(returns, ticker1, ticker2)

    col1, col2, col3 = st.columns(3)
    col1.metric(ticker1, f"{w:.0%}")
    col2.metric(ticker2, f"{1 - w:.0%}")
    col3.metric("Annualised volatility", f"{vol:.2%}")

    fig = plot_portfolio_risk(returns, ticker1, ticker2, w, vol)
    st.pyplot(fig)
    plt.close(fig)

    st.caption(
        f"{len(returns)} daily returns, {start} to {end}. "
        "The optimal weight depends a lot on the window, so try changing it."
    )
