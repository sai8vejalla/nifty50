import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import logging
from datetime import datetime

# 1. Setup & Configuration
yf.utils.get_yf_logger().setLevel(logging.CRITICAL)
st.set_page_config(page_title="Nifty Pro Analyzer", layout="wide")

# Persistent state
if 'data_cache' not in st.session_state:
    st.session_state.data_cache = None

INDICES = {
    "Nifty 50": "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
    "Nifty 100": "https://archives.nseindia.com/content/indices/ind_nifty100list.csv",
    "Nifty 500": "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
    "Nifty Midcap 100": "https://archives.nseindia.com/content/indices/ind_niftymidcap100list.csv",
    "Nifty Smallcap 100": "https://archives.nseindia.com/content/indices/ind_niftysmallcap100list.csv",
}

st.title("🇮🇳 Market Breadth, RS & Momentum Alerts")

with st.sidebar:
    st.header("Analysis Settings")
    selected_index = st.selectbox("Index", list(INDICES.keys()), index=2)
    benchmark = st.selectbox("RS Benchmark", ["^NSEI", "^NSEBANK"])
    fetch_btn = st.button("Run Full Analysis")

if fetch_btn:
    with st.spinner("Processing Market Data..."):
        try:
            # Fetch Tickers
            df_list = pd.read_csv(INDICES[selected_index])
            tickers = [s.strip() + ".NS" for s in df_list['Symbol'] if "DUMMY" not in str(s)]
            
            # Fetch 10 days of data
            data = yf.download(tickers + [benchmark], period="10d", interval="1d", progress=False)['Close']
            
            # 1. Daily Performance
            pct_changes = data[tickers].pct_change() * 100
            latest_pct = pct_changes.iloc[-1].dropna()
            
            # 2. RS Calculation
            rs_ratio = data[tickers].div(data[benchmark], axis=0)
            latest_rs = rs_ratio.pct_change().iloc[-1].dropna() * 100
            
            # 3. 5-Day A/D History
            history = []
            for i in range(-5, 0):
                row = pct_changes.iloc[i].dropna()
                adv = len(row[row > 0])
                dec = len(row[row < 0])
                history.append({
                    "Date": pct_changes.index[i].date(),
                    "Advances": adv,
                    "Declines": dec,
                    "A/D Ratio": round(adv/dec, 2) if dec > 0 else adv
                })
            
            # 4. Momentum Alerts (3 Days Positive)
            # Check if stocks were > 0% for last 3 sessions
            last_3_days = pct_changes.iloc[-3:]
            momentum_stocks = last_3_days.columns[(last_3_days > 0).all()].tolist()
            momentum_data = latest_pct[momentum_stocks].sort_values(ascending=False).head(10)

            st.session_state.data_cache = {
                "abs": latest_pct,
                "rs": latest_rs,
                "history": pd.DataFrame(history),
                "alerts": momentum_data,
                "index_name": selected_index
            }
        except Exception as e:
            st.error(f"Error: {e}")

# --- DISPLAY SECTION ---
if st.session_state.data_cache:
    cache = st.session_state.data_cache
    
    # Trend Analysis 
    latest_ratio = cache['history']["A/D Ratio"].iloc[-1]
    prev_ratio = cache['history']["A/D Ratio"].iloc[-2]
    
    col_a, col_b = st.columns([1, 2])
    with col_a:
        status = "BULLISH" if latest_ratio > 1.2 else "BEARISH" if latest_ratio < 0.8 else "NEUTRAL"
        st.metric("Market Sentiment", status, delta=f"{latest_ratio} A/D Ratio")
    with col_b:
        st.subheader("5-Day A/D History")
        st.line_chart(cache['history'].set_index("Date")["A/D Ratio"])

    # Distribution Charts
    bins = [-100, -5, -4, -3, -2, -1, -0.75, -0.5, -0.25, 0.25, 0.5, 0.75, 1, 2, 3, 4, 5, 100]
    labels = ["<-5%", "-4%", "-3%", "-2%", "-1%", "-0.75%", "-0.5%", "-0.25%", "Flat", "0.25%", "0.5%", "0.75%", "1%", "2%", "3%", "4%", ">5%"]
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Breadth (Absolute)")
        df_abs = pd.cut(cache['abs'], bins=bins, labels=labels).value_counts().reindex(labels).reset_index()
        st.plotly_chart(px.bar(df_abs, x='index', y='Count', text_auto=True, color='index', color_discrete_sequence=px.colors.diverging.RdYlGn[::-1]), use_container_width=True)
    
    with c2:
        st.subheader(f"Relative Strength vs {benchmark}")
        df_rs = pd.cut(cache['rs'], bins=bins, labels=labels).value_counts().reindex(labels).reset_index()
        st.plotly_chart(px.bar(df_rs, x='index', y='Count', text_auto=True, color='index', color_discrete_sequence=px.colors.diverging.Spectral), use_container_width=True)

    # Momentum Alerts
    st.divider()
    st.subheader("🚀 Momentum Alerts: 3-Day Winning Streak")
    if not cache['alerts'].empty:
        st.write("These stocks have closed positive for **3 consecutive days** and are currently showing the strongest gains:")
        st.table(cache['alerts'].reset_index().rename(columns={'index': 'Symbol', 0: 'Today % Change'}))
    else:
        st.info("No stocks found with a 3-day positive streak.")
