import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import data_loader
import portfolio_math

ticker_spy = 'SPY'
ticker_gld = 'GLD'

df_spy = data_loader.get_return(ticker_spy)
df_gld = data_loader.get_return(ticker_gld)

returns = data_loader.combine_df(df_spy, df_gld)

arr = np.array([])
weights = np.array([])

for i in range(101):
    w = i / 100
    arr = np.append(arr, portfolio_math.portfolio_volatility(returns, ticker_spy, ticker_gld, w))
    weights = np.append(weights, w)

plt.plot(weights, arr)
plt.xlabel("SPY Weight")
plt.ylabel("Portfolio Volatility")
plt.title("Portfolio Volatility vs SPY Weight")
plt.grid(True)
plt.show()

