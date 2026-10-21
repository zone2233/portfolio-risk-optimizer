import yfinance as yf
import pandas as pd
from datetime import date


def get_return(ticker: str, start: str | date, end: str | date) -> pd.DataFrame:
    data = yf.download(ticker, start=start, end=end, auto_adjust=True)

    if data.empty:
        raise ValueError(f"No data found for {ticker}")

    daily_returns = (data["Close"] / data["Close"].shift(1)) - 1

    return daily_returns

def combine_df(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    daily_returns = pd.concat([df1, df2], axis=1).dropna()
    return daily_returns

if __name__ == "__main__":
    start = '2025-01-01'
    end = '2026-01-01'

    df_spy = get_return("SPY", start, end)
    df_gld = get_return("GLD", start, end)

    returns = combine_df(df_spy, df_gld)

    print(returns.head())
