import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import logging

# Setup
yf.utils.get_yf_logger().setLevel(logging.CRITICAL)
st.set_page_config(page_title="Nifty Trend & Breadth", layout="wide")

if 'history_df' not in st.session_state:
    st.session_state.history_df = None

INDICES = {
    "Nifty 50": "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
    "Nifty 100": "https://archives.nseindia.com/content/indices/ind_nifty100list.csv",
    "Nifty 500": "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
    "Nifty Midcap 100": "https://archives.nseindia.com/content/indices/ind_niftymidcap100list.csv",
    "Nifty Smallcap 100": "https://archives.nseindia.com/content/indices/ind_niftysmallcap100list.csv",
}

st.title("🇮🇳 Market Breadth, RS & Trend History")

with st.sidebar:
    selected_index = st.selectbox("Select Index", list(INDICES.keys()), index=2)
    benchmark = st.selectbox("Benchmark for RS", ["^NSEI", "^NSEBANK"])
    fetch_btn = st.button("Analyze Trend")

if fetch_btn:
    with st.spinner("Calculating 5-Day Trend..."):
        try:
            df_list = pd.read_csv(INDICES[selected_index])
            tickers = [s.strip() + ".NS" for s in df_list['Symbol'] if "DUMMY" not in str(s)]
            
            # Fetch 10 days of data to safely get 5 days of pct_change
            data = yf.download(tickers + [benchmark], period="10d", interval="1d", progress=False)['Close']
            
            # 1. Current Day Breadth & RS
            pct_change_all = data[tickers].pct_change()
            latest_pct = pct_change_all.iloc[-1] * 100
            
            rs_ratio = data[tickers].div(data[benchmark], axis=0)
            latest_rs = rs_ratio.pct_change().iloc[-1] * 100
            
            # 2. Derive 5-Day History
            history = []
            for i in range(-5, 0):
                daily_change = pct_change_all.iloc[i]
                adv = len(daily_change[daily_change > 0])
                dec = len(daily_change[daily_change < 0])
                history.append({
                    "Date": pct_change_all.index[i].date(),
                    "Advances": adv,
                    "Declines": dec,
                    "A/D Ratio": round(adv/dec, 2) if dec > 0 else adv
                })
            
            st.session_state.data_cache = {"abs": latest_pct.dropna(), "rs": latest_rs.dropna()}
            st.session_state.history_df = pd.DataFrame(history)
            
        except Exception as e:
            st.error(f"Error: {e}")

if st.session_state.history_df is not None:
    # --- SECTION 1: TREND HISTORY ---
    st.subheader("📈 5-Day Sentiment History")
    h_df = st.session_state.history_df
    
    # Visualizing the A/D Trend
    fig_trend = px.line(h_df, x="Date", y="A/D Ratio", text="A/D Ratio", markers=True, title="Advance-Decline Ratio Trend")
    fig_trend.add_hline(y=1.0, line_dash="dash", line_color="gray", annotation_text="Neutral Line")
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # Trend Derivation
    latest_ratio = h_df["A/D Ratio"].iloc[-1]
    prev_ratio = h_df["A/D Ratio"].iloc[-2]
    
    if latest_ratio > 1.5:
        trend_status = "BULLISH"
        trend_color = "green"
    elif latest_ratio < 0.6:
        trend_status = "BEARISH"
        trend_color = "red"
    else:
        trend_status = "NEUTRAL"
        trend_color = "gray"
        
    momentum = "Improving" if latest_ratio > prev_ratio else "Weakening"
    st.markdown(f"### Current Trend: :{trend_color}[{trend_status}] ({momentum} momentum)")

    # --- SECTION 2: BREADTH & RS CHARTS ---
    bins = [-100, -5, -4, -3, -2, -1, -0.75, -0.5, -0.25, 0.25, 0.5, 0.75, 1, 2, 3, 4, 5, 100]
    labels = ["<-5%", "-4%", "-3%", "-2%", "-1%", "-0.75%", "-0.5%", "-0.25%", "Flat", "0.25%", "0.5%", "0.75%", "1%", "2%", "3%", "4%", ">5%"]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Current Day Breadth")
        counts_abs = pd.cut(st.session_state.data_cache["abs"], bins=bins, labels=labels).value_counts().reindex(labels).reset_index()
        st.plotly_chart(px.bar(counts_abs, x='index', y='Count', text_auto=True, color='index', color_discrete_sequence=px.colors.diverging.RdYlGn[::-1]), use_container_width=True)
    
    with col2:
        st.subheader(f"RS vs {benchmark}")
        counts_rs = pd.cut(st.session_state.data_cache["rs"], bins=bins, labels=labels).value_counts().reindex(labels).reset_index()
        st.plotly_chart(px.bar(counts_rs, x='index', y='Count', text_auto=True, color='index', color_discrete_sequence=px.colors.diverging.Spectral), use_container_width=True)
