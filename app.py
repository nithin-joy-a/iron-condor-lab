import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import sqlite3, math
from datetime import date, datetime, timedelta
st.set_page_config(page_title="Iron Condor Pro Lab",page_icon="🧪",layout="wide")
st.title("🧪 Iron Condor Pro Lab")
st.caption("Educational simulator only • Hypothetical positions • No broker connection or live orders")
st.warning("Model estimates only. No live option quotes, Schwab connection, or order execution. Historical data is not a forecast.")

DB="paper_lab.db"
def db():
    return sqlite3.connect(DB,check_same_thread=False)
with db() as c:
    c.execute("""CREATE TABLE IF NOT EXISTS trades(id INTEGER PRIMARY KEY, created TEXT, symbol TEXT, expiry TEXT, contracts INTEGER, lp REAL, sp REAL, sc REAL, lc REAL, credit REAL, iv REAL, rate REAL, entry_spot REAL, status TEXT, notes TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS journal(id INTEGER PRIMARY KEY, created TEXT, trade_id INTEGER, event TEXT, details TEXT)""")
def note(tid,event,details):
    with db() as c: c.execute("INSERT INTO journal(created,trade_id,event,details) VALUES(?,?,?,?)",(datetime.now().isoformat(timespec="seconds"),tid,event,details))
def cdf(x): return .5*(1+math.erf(x/math.sqrt(2)))
def pdf(x): return math.exp(-x*x/2)/math.sqrt(2*math.pi)
def bs(S,K,T,r,v,kind):
    if T<=0:
        return (max(S-K,0) if kind=="call" else max(K-S,0),0,0,0,0)
    v=max(v,1e-6); q=math.sqrt(T); d1=(math.log(S/K)+(r+v*v/2)*T)/(v*q); d2=d1-v*q; disc=math.exp(-r*T)
    if kind=="call":
        p=S*cdf(d1)-K*disc*cdf(d2); delta=cdf(d1); theta=-(S*pdf(d1)*v)/(2*q)-r*K*disc*cdf(d2)
    else:
        p=K*disc*cdf(-d2)-S*cdf(-d1); delta=cdf(d1)-1; theta=-(S*pdf(d1)*v)/(2*q)+r*K*disc*cdf(-d2)
    gamma=pdf(d1)/(S*v*q); vega=S*pdf(d1)*q/100
    return p,delta,gamma,theta/365,vega
def model(S,legs,T,r,v):
    out=np.zeros(5)
    for K,kind,side in legs:
        z=np.array(bs(S,K,T,r,v,kind))*(1 if side=="long" else -1)
        out+=z
    return out
def expiry_pnl(S,lp,sp,sc,lc,credit):
    intrinsic=max(lp-S,0)-max(sp-S,0)-max(S-sc,0)+max(S-lc,0)
    return (credit+intrinsic)*100
def trades():
    with db() as c: return pd.read_sql_query("SELECT * FROM trades ORDER BY id DESC",c)
tabs=st.tabs(["📈 Historical scenarios","🧮 Condor lab","📂 Paper positions","📓 Journal"])
with st.sidebar:
    symbol=st.selectbox("Underlying",["SPX","SPY","QQQ"])
    period=st.selectbox("Historical window",["1mo","3mo","6mo","1y","2y","5y"],index=3)
with tabs[0]:
    st.subheader(symbol+" historical price scenarios")
    tick={"SPX":"^GSPC","SPY":"SPY","QQQ":"QQQ"}[symbol]
    @st.cache_data(ttl=900)
    def history(t,p):
        x=yf.download(t,period=p,interval="1d",auto_adjust=True,progress=False)
        if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
        return x.reset_index() if not x.empty else x
    try: h=history(tick,period)
    except Exception: h=pd.DataFrame()
    if h.empty or "Close" not in h: st.info("Historical data unavailable at the moment. Try again later.")
    else:
        h["return_pct"]=h.Close.pct_change()*100
        ret=h.return_pct.dropna(); last=float(h.Close.iloc[-1])
        a,b,c,d=st.columns(4); a.metric("Latest available close",f"{last:,.2f}"); b.metric("Period high",f"{h.Close.max():,.2f}"); c.metric("Period low",f"{h.Close.min():,.2f}"); d.metric("Annualized daily volatility",f"{ret.std()*np.sqrt(252):.1f}%")
        st.line_chart(h.set_index("Date").Close)
        horizon=st.slider("Historical scenario horizon (trading days)",1,20,5)
        r=h.Close.pct_change(horizon).dropna()
        if len(r):
            qs=r.quantile([.05,.25,.5,.75,.95])
            out=pd.DataFrame({"Percentile":["5th","25th","Median","75th","95th"],"Historical move (%)":qs.values*100,"Illustrative price":last*(1+qs.values)})
            st.dataframe(out.style.format({"Historical move (%)":"{:.2f}%","Illustrative price":"{:,.2f}"}),use_container_width=True,hide_index=True)
        st.caption("Historical samples are not predictions or probability guarantees.")
with tabs[1]:
    st.subheader("Build a hypothetical Iron Condor")
    a,b,c=st.columns(3)
    with a:
        spot=st.number_input("Underlying price",min_value=.01,value=500.0)
        expiry=st.date_input("Expiration",value=date.today()+timedelta(days=30),min_value=date.today())
        n=st.number_input("Number of condors",1,100,1)
    with b:
        lp=st.number_input("Long put strike",min_value=.01,value=480.0)
        sp=st.number_input("Short put strike",min_value=.01,value=490.0)
        sc=st.number_input("Short call strike",min_value=.01,value=510.0)
        lc=st.number_input("Long call strike",min_value=.01,value=520.0)
    with c:
        credit=st.number_input("Net entry credit ($/share)",min_value=.01,value=2.0)
        iv=st.number_input("Assumed flat IV (%)",1.0,300.0,20.0)/100
        rate=st.number_input("Risk-free rate (%)",0.0,20.0,4.0)/100
        thesis=st.text_input("Trade thesis / notes")
    valid=lp<sp<sc<lc and credit<min(sp-lp,lc-sc)
    if not valid: st.error("Require Long Put < Short Put < Short Call < Long Call; credit must be below the narrower wing width.")
    else:
        T=max((expiry-date.today()).days/365,1e-5); legs=[(lp,"put","long"),(sp,"put","short"),(sc,"call","short"),(lc,"call","long")]
        g=model(spot,legs,T,rate,iv); maxp=credit*100*n; maxl=(max(sp-lp,lc-sc)-credit)*100*n
        x1,x2,x3,x4=st.columns(4); x1.metric("Entry credit",f"${maxp:,.2f}"); x2.metric("Max profit",f"${maxp:,.2f}"); x3.metric("Max expiration loss",f"${maxl:,.2f}"); x4.metric("Breakevens",f"{sp-credit:.2f} / {sc+credit:.2f}")
        st.markdown("**Model Greeks for complete condor**")
        gg=st.columns(5)
        for col,label,val in zip(gg,["Delta","Gamma","Theta / day","Vega / vol point","Model P&L now"],[g[1]*100*n,g[2]*100*n,g[3]*100*n,g[4]*100*n,(credit+g[0])*100*n]):
            col.metric(label,f"{val:.4f}" if label in ["Delta","Gamma"] else f"${val:.2f}")
        st.caption("European Black–Scholes with one flat IV. Theta is per calendar day; vega is per 1 volatility point. These are estimates, not executable quotes.")
        st.markdown("**Before-expiration what-if**")
        move=st.slider("Underlying price change (%)",-20.0,20.0,0.0,.5)
        ivmove=st.slider("IV change (percentage points)",-15.0,30.0,0.0,.5)
        elapsed=st.slider("Days elapsed",0,max((expiry-date.today()).days,1),min(5,max((expiry-date.today()).days,1)))
        future_spot=spot*(1+move/100); future_T=max((expiry-date.today()).days-elapsed,0)/365; future_iv=max(.01,iv+ivmove/100)
        future=model(future_spot,legs,future_T,rate,future_iv)
        whatif=(credit+future[0])*100*n
        st.metric("Hypothetical what-if P&L",f"${whatif:,.2f}",delta=f"${whatif-(credit+g[0])*100*n:,.2f} vs current model mark")
        grid=np.linspace(max(.01,lp-(lc-lp)),lc+(lc-lp),300)
        st.line_chart(pd.DataFrame({"Expiration P&L ($)":[expiry_pnl(x,lp,sp,sc,lc,credit)*n for x in grid]},index=grid))
        if st.button("Save as open paper position",type="primary"):
            with db() as con:
                cur=con.execute("INSERT INTO trades(created,symbol,expiry,contracts,lp,sp,sc,lc,credit,iv,rate,entry_spot,status,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (datetime.now().isoformat(timespec="seconds"),symbol,str(expiry),int(n),lp,sp,sc,lc,credit,iv,rate,spot,"Open",thesis))
                tid=cur.lastrowid
            note(tid,"Opened paper position",thesis or "Saved from Condor Lab"); st.success(f"Saved hypothetical position #{tid}.")
with tabs[2]:
    st.subheader("Paper positions")
    t=trades()
    if t.empty: st.info("No positions yet. Save one from the Condor Lab.")
    else:
        filt=st.selectbox("Filter status",["All","Open","Closed"])
        st.dataframe(t if filt=="All" else t[t.status==filt],use_container_width=True,hide_index=True)
        ids=t.id.tolist(); tid=st.selectbox("Position ID to update",ids); status=st.selectbox("Set status",["Open","Closed"]); detail=st.text_input("Update note")
        if st.button("Update paper status"):
            with db() as con: con.execute("UPDATE trades SET status=? WHERE id=?",(status,int(tid)))
            note(int(tid),"Status changed to "+status,detail); st.success("Updated."); st.rerun()
        x,y=st.columns(2); x.metric("Open positions",int((t.status=="Open").sum())); y.metric("Closed positions",int((t.status=="Closed").sum()))
        st.caption("Status changes do not imply an exit fill or realized profit/loss. Record exit data separately in your notes.")
with tabs[3]:
    st.subheader("Trade journal & activity dashboard")
    t=trades()
    with db() as con: j=pd.read_sql_query("SELECT * FROM journal ORDER BY id DESC",con)
    if not j.empty: st.dataframe(j,use_container_width=True,hide_index=True)
    else: st.info("Journal entries will appear when you save or update positions.")
    if not t.empty:
        st.metric("Total saved positions",len(t))
        st.bar_chart(t.groupby(["symbol","status"]).size().unstack(fill_value=0))
    memo=st.text_area("Add research note")
    if st.button("Save research note"):
        note(None,"Research note",memo); st.success("Saved."); st.rerun()
st.divider()
st.caption("Data source: Yahoo Finance via yfinance when available. Local SQLite persistence on hosted free services may not survive restarts. Export/back up records. No real-money trading or investment advice.")
