# Iron Condor Paper-Trading Lab

A small Streamlit educational simulator for SPX, SPY, and QQQ iron condors.

## What it does
- Accepts hypothetical strikes and option premiums.
- Calculates net credit, expiration breakevens, max profit, and max expiration loss.
- Shows an expiration payoff chart and scenario table.
- Exports the current hypothetical scenario to CSV.

## Important limitations
- No Schwab connection, API keys, brokerage login, live quotes, or order placement.
- No Greeks, implied volatility surface, early assignment, commissions, slippage, taxes, or intraday mark-to-market.
- Uses a simplified 1:1:1:1 iron-condor payoff at expiration.
- Verify actual contract specifications and settlement details independently.

## Run in Google Colab
1. Upload `app.py` and `requirements.txt` to a GitHub repository (or upload the ZIP and extract it).
2. In Colab, run:

```python
!pip install -r requirements.txt
!python - <<'PY'
import importlib.util
spec = importlib.util.spec_from_file_location("app", "app.py")
print("App file is present. Launch it with Streamlit on a hosted service.")
PY
```

Colab is useful for experimenting with Python calculations, but it is not a reliable always-on host for a Streamlit web app.

## Deploy on Streamlit Community Cloud
1. Create a GitHub repository and upload `app.py` and `requirements.txt` to its root.
2. Sign in at https://share.streamlit.io/ with GitHub.
3. Select **Create app**, choose your repository, branch, and `app.py`.
4. Deploy. Open the generated app URL on your Android phone.

The free Community Cloud service has resource and sleep limitations. Do not treat it as a guaranteed continuous-running service.
