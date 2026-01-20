import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import logging

# 1. Setup
yf.utils.get_yf_logger().setLevel(logging.CRITICAL)
st.set_page_config(page_title="Indian Market Analyzer", layout="wide")

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
            
            raw_data = yf.download(tickers + [benchmark], period="5d", interval="1d", progress=False)['Close']
            
            # Absolute % Change
            abs_change = raw_data[tickers].pct_change().iloc[-1] * 100
            
            # Relative Strength % Change
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

# 5. Visualization with Labels
if st.session_state.data_cache:
    cache = st.session_state.data_cache
    
    # 18 edges = 17 labels
    bins = [-100, -5, -4, -3, -2, -1, -0.75, -0.5, -0.25, 0.25, 0.5, 0.75, 1, 2, 3, 4, 5, 100]
    labels = ["<-5%", "-4%", "-3%", "-2%", "-1%", "-0.75%", "-0.5%", "-0.25%", "Flat", 
              "0.25%", "0.5%", "0.75%", "1%", "2%", "3%", "4%", ">5%"]

    def create_distribution_df(series):
        # Convert series to categories
        counts = pd.cut(series, bins=bins, labels=labels).value_counts().reindex(labels).reset_index()
        counts.columns = ['Range', 'Count']
        return counts

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"📊 {cache['index_name']} Breadth")
        df_abs = create_distribution_df(cache['abs'])
        # text_auto=True shows the count on the bar
        fig_abs = px.bar(df_abs, x='Range', y='Count', color='Range', text_auto=True,
                         color_discrete_sequence=px.colors.diverging.RdYlGn[::-1])
        st.plotly_chart(fig_abs, use_container_width=True)

    with col2:
        st.subheader(f"💪 RS vs {cache['bench_name']}")
        df_rs = create_distribution_df(cache['rs'])
        # text_auto=True shows the count on the bar
        fig_rs = px.bar(df_rs, x='Range', y='Count', color='Range', text_auto=True,
                        color_discrete_sequence=px.colors.diverging.Spectral)
        st.plotly_chart(fig_rs, use_container_width=True)
    
    # Display the summary table below
    st.divider()
    st.subheader("📋 Category Count Summary")
    summary_df = df_abs.rename(columns={'Count': 'Absolute Count'})
    summary_df['RS Count'] = df_rs['Count']
    st.table(summary_df) # Static table for quick reference
