import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import logging

# 1. Initialization & Session State
yf.utils.get_yf_logger().setLevel(logging.CRITICAL)
st.set_page_config(page_title="Indian Market Breadth & RS", layout="wide")

if 'pct_data' not in st.session_state:
    st.session_state.pct_data = None
if 'rs_data' not in st.session_state:
    st.session_state.rs_data = None

# 2. Index Configuration
INDICES = {
    "Nifty 50": "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
    "Nifty 100": "https://archives.nseindia.com/content/indices/ind_nifty100list.csv",
    "Nifty 500": "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
    "Nifty Midcap 100": "https://archives.nseindia.com/content/indices/ind_niftymidcap100list.csv",
    "Nifty Smallcap 100": "https://archives.nseindia.com/content/indices/ind_niftysmallcap100list.csv",
    "Nifty Bank": "https://archives.nseindia.com/content/indices/ind_niftybanklist.csv",
}

st.title("🇮🇳 Indian Market Breadth & Relative Strength")

# 3. Sidebar
selected_index = st.sidebar.selectbox("Select Target Index", list(INDICES.keys()), index=2)
benchmark = st.sidebar.selectbox("Compare RS against", ["^NSEI", "^NSEBANK"], help="^NSEI is Nifty 50")
fetch_btn = st.sidebar.button("Fetch Analysis")

# 4. Processing
if fetch_btn:
    with st.spinner("Downloading Market Data..."):
        try:
            df_list = pd.read_csv(INDICES[selected_index])
            tickers = [s + ".NS" for s in df_list['Symbol'] if "DUMMY" not in str(s)]
            
            # Fetch data for stocks + benchmark
            data = yf.download(tickers + [benchmark], period="5d", interval="1d", progress=False)['Close']
            
            # 1-Day % Change
            st.session_state.pct_data = data[tickers].pct_change().iloc[-1] * 100
            
            # Relative Strength (Stock / Benchmark)
            rs_ratio = data[tickers].div(data[benchmark], axis=0)
            st.session_state.rs_data = rs_ratio.pct_change().iloc[-1] * 100
            
            st.success("Analysis Complete!")
        except Exception as e:
            st.error(f"Error: {e}")

# 5. Fixed Binning Logic
if st.session_state.pct_data is not None:
    # 18 edges = 17 labels
    bins = [-100, -5, -4, -3, -2, -1, -0.75, -0.5, -0.25, 0.25, 0.5, 0.75, 1, 2, 3, 4, 5, 100]
    labels = ["Down >5%", "Down 4-5%", "Down 3-4%", "Down 2-3%", "Down 1-2%", "-0.75%", "-0.5%", "-0.25%", 
              "Flat", "0.25%", "0.5%", "0.75%", "1%", "2%", "3%", "4%", "5%", "Up >5%"]
    
    # Fix: Ensure labels matches gaps between bin edges
    # Updated labels list to exactly 17 items
    labels = ["<-5%", "-4%", "-3%", "-2%", "-1%", "-0.75%", "-0.5%", "-0.25%", "Flat", 
              "0.25%", "0.5%", "0.75%", "1%", "2%", "3%", "4%", ">5%"]

    def get_counts(series):
        return pd.cut(series.dropna(), bins=bins, labels=labels).value_counts().reindex(labels).reset_index()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"📊 {selected_index} Breadth")
        df_b = get_counts(st.session_state.pct_data)
        st.plotly_chart(px.bar(df_b, x='index', y='Count', color='index', 
                               color_discrete_sequence=px.colors.diverging.RdYlGn[::-1]), use_container_width=True)

    with col2:
        st.subheader(f"💪 RS vs {benchmark}")
        df_rs = get_counts(st.session_state.rs_data)
        st.plotly_chart(px.bar(df_rs, x='index', y='Count', color='index', 
                               color_discrete_sequence=px.colors.diverging.Spectral), use_container_width=True)
