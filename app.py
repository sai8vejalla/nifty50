import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import logging

# Silence background logs
yf.utils.get_yf_logger().setLevel(logging.CRITICAL)

st.set_page_config(page_title="Indian Market Breadth & RS", layout="wide")

# 1. Dictionary of NSE CSV Links
INDICES = {
    "Nifty 50": "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
    "Nifty Next 50": "https://archives.nseindia.com/content/indices/ind_niftynext50list.csv",
    "Nifty 100": "https://archives.nseindia.com/content/indices/ind_nifty100list.csv",
    "Nifty 500": "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
    "Nifty Midcap 100": "https://archives.nseindia.com/content/indices/ind_niftymidcap100list.csv",
    "Nifty Smallcap 100": "https://archives.nseindia.com/content/indices/ind_niftysmallcap100list.csv",
    "Nifty Bank": "https://archives.nseindia.com/content/indices/ind_niftybanklist.csv",
}

st.title("🇮🇳 Indian Market Breadth & Relative Strength")

# 2. Sidebar for Controls
with st.sidebar:
    st.header("App Controls")
    selected_index = st.selectbox("Select Target Index", list(INDICES.keys()), index=3) # Default Nifty 500
    benchmark_index = st.selectbox("Compare RS against (Benchmark)", ["^NSEI", "^NSEBANK"], help="^NSEI is Nifty 50")
    refresh = st.button("Fetch Analysis")

# 3. Calculation Logic
if refresh:
    with st.spinner(f"Analyzing {selected_index}..."):
        try:
            # Load Tickers
            df_list = pd.read_csv(INDICES[selected_index])
            tickers = [s + ".NS" for s in df_list['Symbol'] if "DUMMY" not in str(s)]
            
            # Fetch Index and Benchmark Data
            # We fetch 30 days to calculate a more stable Relative Strength
            all_data = yf.download(tickers + [benchmark_index], period="30d", interval="1d", progress=False, auto_adjust=True)
            
            if not all_data.empty:
                prices = all_data['Close']
                
                # Daily Breadth (1-Day % Change)
                pct_change = prices[tickers].pct_change().iloc[-1] * 100
                pct_change = pct_change.dropna()

                # Relative Strength Calculation: (Stock Price / Benchmark Price)
                # Then calculate the % change of that ratio over 1 day
                rs_ratio = prices[tickers].div(prices[benchmark_index], axis=0)
                rs_pct_change = rs_ratio.pct_change().iloc[-1] * 100
                rs_pct_change = rs_pct_change.dropna()

                # --- UI DISPLAY ---
                m1, m2 = st.columns(2)
                with m1:
                    st.subheader(f"📊 {selected_index} 1-Day Change")
                    bins = [-100, -5, -4, -3, -2, -1, -0.75, -0.5, -0.25, 0.25, 0.5, 0.75, 1, 2, 3, 4, 5, 100]
                    labels = ["<-5%", "-4%", "-3%", "-2%", "-1%", "-0.75%", "-0.5%", "-0.25%", "Flat", 
                              "0.25%", "0.5%", "0.75%", "1%", "2%", "3%", "4%", "5%", ">5%"]
                    
                    df_counts = pd.cut(pct_change, bins=bins, labels=labels).value_counts().reindex(labels).reset_index()
                    fig1 = px.bar(df_counts, x='index', y='Count', color='index', color_discrete_sequence=px.colors.diverging.RdYlGn[::-1])
                    st.plotly_chart(fig1, use_container_width=True)

                with m2:
                    st.subheader(f"💪 RS vs {benchmark_index} (Outperformance)")
                    # This tells you how many stocks beat the Nifty 50 today
                    rs_counts = pd.cut(rs_pct_change, bins=bins, labels=labels).value_counts().reindex(labels).reset_index()
                    fig2 = px.bar(rs_counts, x='index', y='Count', color='index', color_discrete_sequence=px.colors.diverging.Spectral)
                    st.plotly_chart(fig2, use_container_width=True)

                st.success(f"Breadth Analysis: {len(pct_change[pct_change > 0])} stocks Advanced | {len(pct_change[pct_change < 0])} Declined")
            else:
                st.error("No data found from Yahoo Finance.")
        except Exception as e:
            st.error(f"Error: {e}")
else:
    st.info("Click 'Fetch Analysis' to see the market distribution and relative strength.")
