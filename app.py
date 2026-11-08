import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date

st.set_page_config(page_title="Iron Condor Paper Lab", page_icon="🧪", layout="wide")

st.title("🧪 Iron Condor Paper-Trading Lab")
st.caption("Educational simulator only • Hypothetical inputs • No broker connection • No live orders")

st.warning(
    "This app does not fetch live quotes or place trades. Enter hypothetical option premiums and "
    "strikes. Results are simplified expiration scenarios before commissions, fees, slippage, taxes, "
    "early assignment, and settlement effects."
)

def condor_pnl(spot, lp, sp, sc, lc, credit, multiplier=100):
    """Expiration P&L for a 1:1:1:1 iron condor, per contract."""
    spot = np.asarray(spot, dtype=float)
    intrinsic = (
        np.maximum(lp - spot, 0)
        - np.maximum(sp - spot, 0)
        - np.maximum(spot - sc, 0)
        + np.maximum(spot - lc, 0)
    )
    return (credit + intrinsic) * multiplier

with st.sidebar:
    st.header("Contract details")
    symbol = st.selectbox("Underlying", ["SPX", "SPY", "QQQ"])
    multiplier = st.selectbox("Contract multiplier", [100], index=0)
    contracts = st.number_input("Number of condors", min_value=1, max_value=100, value=1, step=1)
    expiry = st.date_input("Hypothetical expiration", value=date.today())
    st.caption("For standard listed options, the multiplier is commonly 100. Verify contract specifications independently.")

st.subheader("1. Enter a hypothetical Iron Condor")
c1, c2 = st.columns(2)
with c1:
    st.markdown("**Put spread**")
    lp = st.number_input("Long put strike", min_value=0.01, value=490.0, step=1.0)
    sp = st.number_input("Short put strike", min_value=0.01, value=500.0, step=1.0)
    lprem = st.number_input("Long put premium (per share)", min_value=0.0, value=1.00, step=0.05)
    sprem = st.number_input("Short put premium (per share)", min_value=0.0, value=2.50, step=0.05)
with c2:
    st.markdown("**Call spread**")
    sc = st.number_input("Short call strike", min_value=0.01, value=520.0, step=1.0)
    lc = st.number_input("Long call strike", min_value=0.01, value=530.0, step=1.0)
    screm = st.number_input("Short call premium (per share)", min_value=0.0, value=2.50, step=0.05)
    lcrem = st.number_input("Long call premium (per share)", min_value=0.0, value=1.00, step=0.05)

valid = lp < sp < sc < lc
credit = sprem + screm - lprem - lcrem
put_width = sp - lp
call_width = lc - sc
max_wing = max(put_width, call_width)
valid = valid and credit > 0 and credit < max_wing

if not valid:
    st.error("Check your inputs: strikes must satisfy Long Put < Short Put < Short Call < Long Call. Net credit must be positive and smaller than the widest spread.")
else:
    max_profit = credit * multiplier * contracts
    put_max_loss = (put_width - credit) * multiplier * contracts
    call_max_loss = (call_width - credit) * multiplier * contracts
    max_loss = max_wing - credit
    lower_be = sp - credit
    upper_be = sc + credit

    st.subheader("2. Hypothetical trade summary")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Net credit", f"${credit:.2f}/share")
    m2.metric("Maximum profit", f"${max_profit:,.2f}")
    m3.metric("Maximum expiration loss", f"${max_loss * multiplier * contracts:,.2f}")
    m4.metric("Breakeven range", f"{lower_be:.2f} – {upper_be:.2f}")

    st.caption(
        f"Put-side maximum loss: ${put_max_loss:,.2f} • "
        f"Call-side maximum loss: ${call_max_loss:,.2f} • "
        f"Underlying: {symbol} • Contracts: {contracts} • Expiration: {expiry}"
    )

    st.subheader("3. Expiration scenario")
    center = (lp + lc) / 2
    default_spot = float(center)
    spot_at_expiry = st.number_input(
        "Hypothetical underlying price at expiration",
        min_value=0.01, value=default_spot, step=1.0
    )
    scenario_pnl = float(condor_pnl(spot_at_expiry, lp, sp, sc, lc, credit, multiplier) * contracts)
    st.metric("Simulated expiration P&L", f"${scenario_pnl:,.2f}")

    st.subheader("4. Payoff diagram at expiration")
    low = max(0.01, lp - max_wing * 1.5)
    high = lc + max_wing * 1.5
    spots = np.linspace(low, high, 400)
    pnls = condor_pnl(spots, lp, sp, sc, lc, credit, multiplier) * contracts

    fig, ax = plt.subplots()
    ax.plot(spots, pnls, label="Expiration P&L")
    ax.axhline(0, linewidth=1)
    ax.axvline(lower_be, linestyle="--", label="Lower breakeven")
    ax.axvline(upper_be, linestyle="--", label="Upper breakeven")
    ax.axvline(spot_at_expiry, linestyle=":", label="Scenario price")
    ax.set_xlabel(f"{symbol} price at expiration")
    ax.set_ylabel("Hypothetical P&L ($)")
    ax.set_title("Iron Condor expiration payoff")
    ax.grid(True, alpha=0.3)
    ax.legend()
    st.pyplot(fig)
    plt.close(fig)

    st.subheader("5. Scenario table")
    scenario_prices = sorted(set([
        round(max(0.01, lp), 2), round(lower_be, 2), round(sp, 2),
        round((sp + sc) / 2, 2), round(sc, 2), round(upper_be, 2),
        round(lc, 2), round(spot_at_expiry, 2)
    ]))
    scenario_df = pd.DataFrame({
        f"{symbol} at expiration": scenario_prices,
        "Hypothetical P&L ($)": [
            round(float(condor_pnl(x, lp, sp, sc, lc, credit, multiplier) * contracts), 2)
            for x in scenario_prices
        ]
    })
    st.dataframe(scenario_df, use_container_width=True, hide_index=True)

    trade = {
        "symbol": symbol, "expiration": str(expiry), "contracts": contracts,
        "long_put": lp, "short_put": sp, "short_call": sc, "long_call": lc,
        "net_credit_per_share": round(credit, 4),
        "max_profit_dollars": round(max_profit, 2),
        "max_expiration_loss_dollars": round(max_loss * multiplier * contracts, 2),
        "lower_breakeven": round(lower_be, 4), "upper_breakeven": round(upper_be, 4),
        "scenario_underlying_at_expiration": spot_at_expiry,
        "scenario_pnl_dollars": round(scenario_pnl, 2)
    }
    csv = pd.DataFrame([trade]).to_csv(index=False).encode("utf-8")
    st.download_button("Download this hypothetical scenario (CSV)", csv, "iron_condor_scenario.csv", "text/csv")

st.divider()
st.subheader("How to use this safely")
st.markdown(
    """
    1. Use made-up strikes and premiums first to learn the payoff mechanics.
    2. Change one input at a time and observe how the payoff diagram changes.
    3. Compare put-side and call-side maximum losses when the wings are unequal.
    4. Remember this is an expiration-only model, not a pricing model for changing option values before expiration.
    """
)
st.caption("Educational tool only. Not investment advice. No live market data, account access, or order execution.")
