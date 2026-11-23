
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="My Options Trading AI", layout="wide")

st.title("🇮🇳 My Options Trading AI")
st.caption("Market Analysis • Signals • Risk Management • Paper Trading")

symbol = st.sidebar.selectbox(
    "Market",
    ["^NSEI", "^BSESN"],
    format_func=lambda x: "NIFTY 50" if x == "^NSEI" else "SENSEX"
)

capital = st.sidebar.number_input("Capital (₹)", min_value=1000, value=100000, step=1000)
risk_pct = st.sidebar.slider("Risk per trade (%)", 0.5, 2.0, 1.0, 0.5)
premium = st.sidebar.number_input("Option Premium (₹)", min_value=1.0, value=100.0)
lot_size = st.sidebar.number_input("Lot Size", min_value=1, value=65)
stop_pct = st.sidebar.slider("Stop Loss (%)", 5, 50, 20)
target_pct = st.sidebar.slider("Target (%)", 5, 100, 40)

@st.cache_data(ttl=60)
def get_data(ticker):
    df = yf.download(ticker, period="5d", interval="5m", progress=False)
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df["EMA9"] = df["Close"].ewm(span=9).mean()
    df["EMA21"] = df["Close"].ewm(span=21).mean()
    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))
    return df.dropna()

try:
    df = get_data(symbol)

    if df.empty:
        st.error("Market data unavailable. Please retry.")
        st.stop()

    price = float(df["Close"].iloc[-1])
    ema9 = float(df["EMA9"].iloc[-1])
    ema21 = float(df["EMA21"].iloc[-1])
    rsi = float(df["RSI"].iloc[-1])

    if ema9 > ema21 and rsi > 50:
        signal = "CALL WATCH"
    elif ema9 < ema21 and rsi < 50:
        signal = "PUT WATCH"
    else:
        signal = "WAIT"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Market Price", f"₹{price:,.2f}")
    c2.metric("EMA 9", f"{ema9:,.2f}")
    c3.metric("EMA 21", f"{ema21:,.2f}")
    c4.metric("RSI", f"{rsi:.2f}")

    st.subheader("AI Market Signal")
    if signal == "CALL WATCH":
        st.success("🟢 CALL WATCH")
    elif signal == "PUT WATCH":
        st.error("🔴 PUT WATCH")
    else:
        st.warning("🟡 WAIT / NO TRADE")

    chart = df[["Close", "EMA9", "EMA21"]].tail(100)
    st.line_chart(chart)

    st.subheader("Risk Management Calculator")

    risk_amount = capital * risk_pct / 100
    sl_premium = premium * (1 - stop_pct / 100)
    target_premium = premium * (1 + target_pct / 100)
    loss_per_lot = (premium - sl_premium) * lot_size
    lots = int(risk_amount / loss_per_lot) if loss_per_lot > 0 else 0

    r1, r2, r3 = st.columns(3)
    r1.metric("Risk Budget", f"₹{risk_amount:,.0f}")
    r2.metric("Stop Loss Premium", f"₹{sl_premium:.2f}")
    r3.metric("Target Premium", f"₹{target_premium:.2f}")

    r4, r5, r6 = st.columns(3)
    r4.metric("Lots (Risk Based)", lots)
    r5.metric("Quantity", lots * lot_size)
    r6.metric("Estimated Max Loss", f"₹{lots * loss_per_lot:,.2f}")

    st.subheader("Paper Trading Journal")

    if "trades" not in st.session_state:
        st.session_state.trades = []

    with st.form("paper_trade"):
        direction = st.selectbox("Trade", ["CALL", "PUT"])
        entry = st.number_input("Entry Premium", min_value=0.0, value=float(premium))
        exit_price = st.number_input("Exit Premium", min_value=0.0, value=float(premium))
        quantity = st.number_input("Quantity", min_value=1, value=int(lot_size))
        submitted = st.form_submit_button("Save Paper Trade")

        if submitted:
            pnl = (exit_price - entry) * quantity
            if direction == "PUT":
                pnl = (exit_price - entry) * quantity
            st.session_state.trades.append({
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Type": direction,
                "Entry": entry,
                "Exit": exit_price,
                "Qty": quantity,
                "P&L": round(pnl, 2)
            })
            st.success("Paper trade saved!")

    if st.session_state.trades:
        journal = pd.DataFrame(st.session_state.trades)
        st.dataframe(journal, use_container_width=True)
        st.metric("Paper Trading P&L", f"₹{journal['P&L'].sum():,.2f}")
        st.download_button(
            "Download Journal CSV",
            journal.to_csv(index=False),
            "paper_trading_journal.csv",
            "text/csv"
        )
    else:
        st.info("No paper trades recorded yet.")

    st.caption("Last updated: " + datetime.now().strftime("%d-%m-%Y %H:%M:%S"))

except Exception as e:
    st.error(f"Unable to load market data: {e}")

st.divider()
st.caption("Educational tool only. Signals are not guaranteed. No live orders are placed.")
