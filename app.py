import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import logging

# 1. Setup
yf.utils.get_yf_logger().setLevel(logging.CRITICAL)
st.set_page_config(page_title="Indian Market Analyzer", layout="wide")

# Persistent storage to prevent output from disappearing
if 'data_cache' not in st.session_state:
    st.session_state.data_cache = None

# 2. Index Configuration
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

# 3. Sidebar
with st.sidebar:
    st.header("Controls")
    selected_index = st.selectbox("Select Index", list(INDICES.keys()), index=3)
    benchmark = st.selectbox("Benchmark for RS", ["^NSEI", "^NSEBANK"])
    fetch_btn = st.button("Run Analysis")

# 4. Data Processing
if fetch_btn:
    with st.spinner("Downloading data..."):
        try:
            df_list = pd.read_csv(INDICES[selected_index])
            tickers = [s.strip() + ".NS" for s in df_list['Symbol'] if "DUMMY" not in str(s)]
            
            # Fetch prices for stocks and benchmark
            raw_data = yf.download(tickers + [benchmark], period="5d", interval="1d", progress=False)['Close']
            
            # Calculate Absolute % Change
            abs_change = raw_data[tickers].pct_change().iloc[-1] * 100
            
            # Calculate RS % Change (Price Ratio vs Benchmark)
            rs_ratio = raw_data[tickers].div(raw_data[benchmark], axis=0)
            rs_change = rs_ratio.pct_change().iloc[-1] * 100
            
            st.session_state.data_cache = {
                "abs": abs_change.dropna(),
                "rs": rs_change.dropna(),
                "index_name": selected_index,
                "bench_name": benchmark
            }
        except Exception as e:
            st.error(f"Error: {e}")

# 5. Visualization (Resolving the Label Error)
if st.session_state.data_cache:
    cache = st.session_state.data_cache
    
    # Define EXACTLY 18 edges
    bins = [-100, -5, -4, -3, -2, -1, -0.75, -0.5, -0.25, 0.25, 0.5, 0.75, 1, 2, 3, 4, 5, 100]
    
    # Define EXACTLY 17 labels to match the gaps
    labels = [
        "<-5%", "-4%", "-3%", "-2%", "-1%", 
        "-0.75%", "-0.5%", "-0.25%", "Flat", 
        "0.25%", "0.5%", "0.75%", "1%", 
        "2%", "3%", "4%", ">5%"
    ]

    def create_distribution_df(series):
        counts = pd.cut(series, bins=bins, labels=labels).value_counts().reindex(labels).reset_index()
        counts.columns = ['Range', 'Count']
        return counts

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"📊 {cache['index_name']} Breadth")
        df_abs = create_distribution_df(cache['abs'])
        st.plotly_chart(px.bar(df_abs, x='Range', y='Count', color='Range', 
                               color_discrete_sequence=px.colors.diverging.RdYlGn[::-1]), use_container_width=True)

    with col2:
        st.subheader(f"💪 RS vs {cache['bench_name']}")
        df_rs = create_distribution_df(cache['rs'])
        st.plotly_chart(px.bar(df_rs, x='Range', y='Count', color='Range', 
                               color_discrete_sequence=px.colors.diverging.Spectral), use_container_width=True)
    
    st.info(f"Analysis based on {len(cache['abs'])} stocks from {cache['index_name']}")
