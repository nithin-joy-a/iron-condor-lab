# Iron Condor Pro Lab

Educational Streamlit paper simulator for SPX, SPY and QQQ.

## Features
- Historical daily prices and empirical multi-day return scenarios via yfinance.
- Black-Scholes theoretical values and model Greeks: Delta, Gamma, Theta and Vega.
- Before-expiration what-if analysis changing spot, IV and elapsed days.
- SQLite paper position tracking, status updates, trade journal and activity dashboard.
- Expiration payoff chart.

## Android deployment
1. Extract this ZIP.
2. Upload `app.py` and `requirements.txt` to the root of a GitHub repository.
3. Go to https://share.streamlit.io/, sign in with GitHub, create an app and select `app.py`.
4. Deploy and open the generated URL in Chrome on Android.

## Important limitations
No Schwab API, brokerage credentials, real-time option chain, or order execution. Premium and IV are assumptions. Greeks and pre-expiration P&L are Black-Scholes estimates using one flat IV. The model omits volatility skew, dividends, early exercise/assignment, bid/ask, fees, slippage, taxes and contract-specific settlement nuances. Historical returns are not forecasts. The app's local SQLite database may not persist through hosted service restarts. Educational use only, not investment advice.
