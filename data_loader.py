import yfinance as yf
import pandas as pd

ticker_spy = 'SPY'
ticker_gld = 'GLD'

data_spy = yf.download(ticker_spy, start='2020-01-01', end='2026-01-01', auto_adjust = True)
data_gld = yf.download(ticker_gld, start='2020-01-01', end='2026-01-01', auto_adjust = True)

#print(data_spy.head())
#print(data_gld.head())

daily_returns_spy = (data_spy['Close'] / data_spy['Close'].shift(1)) - 1
daily_returns_spy = daily_returns_spy.rename(columns = {'SPY': 'daily_returns_spy'})

daily_returns_gld = (data_gld['Close'] / data_gld['Close'].shift(1)) - 1
daily_returns_gld = daily_returns_gld.rename(columns = {'GLD': 'daily_returns_gld'})

#print(daily_returns_spy.head())
#print(daily_returns_gld.head())

daily_returns = pd.concat([daily_returns_spy, daily_returns_gld], axis=1).dropna()

print(daily_returns.head())
print(daily_returns.isna().sum())