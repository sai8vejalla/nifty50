import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import logging
from datetime import datetime

# Silence background error logs
yf.utils.get_yf_logger().setLevel(logging.CRITICAL)

st.set_page_config(page_title="Nifty Breadth Analyzer", layout="wide")

# Persistent data storage so output doesn't disappear
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'selected_index_name' not in st.session_state:
    st.session_state.selected_index_name = ""

# 1. Expanded Index Configuration
INDICES = {
    "Nifty 50": "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
    "Nifty Next 50": "https://archives.nseindia.com/content/indices/ind_niftynext50list.csv",
    "Nifty 100": "https://archives.nseindia.com/content/indices/ind_nifty100list.csv",
    "Nifty 200": "https://archives.nseindia.com/content/indices/ind_nifty200list.csv",
    "Nifty 500": "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
    "Nifty Midcap 50": "https://archives.nseindia.com/content/indices/ind_niftymidcap50list.csv",
    "Nifty Midcap 100": "https://archives.nseindia.com/content/indices/ind_niftymidcap100list.csv",
    "Nifty Midcap 150": "https://www.niftyindices.com/IndexConstituent/ind_niftymidcap150list.csv",
    "Nifty Smallcap 50": "https://archives.nseindia.com/content/indices/ind_niftysmallcap50list.csv",
    "Nifty Smallcap 100": "https://archives.nseindia.com/content/indices/ind_niftysmallcap100list.csv",
    "Nifty Smallcap 250": "https://www.niftyindices.com/IndexConstituent/ind_niftysmallcap250list.csv",
    "Nifty Bank": "https://archives.nseindia.com/content/indices/ind_niftybanklist.csv",
    "Nifty IT": "https://archives.nseindia.com/content/indices/ind_niftyitlist.csv",
}

st.title("🇮🇳 Indian Market Advance-Decline Dashboard")
st.markdown("Analyze market breadth across Large, Mid, and Small-cap indices.")

# 2. Sidebar Controls
with st.sidebar:
    st.header("Search Settings")
    selected_index = st.selectbox("Choose Index", list(INDICES.keys()))
    run_button = st.button("Fetch & Analyze Data")

# 3. Backend Logic
if run_button:
    with st.spinner(f"Analyzing {selected_index}..."):
        try:
            df_list = pd.read_csv(INDICES[selected_index])
            tickers = [str(s).strip() + ".NS" for s in df_list['Symbol'] if "DUMMY" not in str(s)]
            
            # Fetch 2 days of data for daily % change
            data = yf.download(tickers, period="2d", interval="1d", progress=False, auto_adjust=True)
            
            if not data.empty and 'Close' in data:
                pct_change = data['Close'].pct_change().iloc[-1] * 100
                st.session_state.analysis_result = pct_change.dropna()
                st.session_state.selected_index_name = selected_index
            else:
                st.error("No data found. Yahoo Finance may be rate-limiting or the market is closed.")
        except Exception as e:
            st.error(f"Error fetching data: {e}")

# 4. Frontend Display (Displays whenever session state has data)
if st.session_state.analysis_result is not None:
    res = st.session_state.analysis_result
    
    # Summary Metrics
    adv, dec = len(res[res > 0]), len(res[res < 0])
    m1, m2, m3 = st.columns(3)
    m1.metric("Advances", adv)
    m2.metric("Declines", dec)
    m3.metric("A/D Ratio", round(adv/dec, 2) if dec > 0 else "Bullish")

    # Granular Binning (including .25, .5, .75)
    bins = [-100, -5, -4, -3, -2, -1, -0.75, -0.5, -0.25, 0.25, 0.5, 0.75, 1, 2, 3, 4, 5, 100]
    labels = ["Down >5%", "Down 4-5%", "Down 3-4%", "Down 2-3%", "Down 1-2%", 
              "Down 0.75-1%", "Down 0.5-0.75%", "Down 0.25-0.5%", "Flat (-0.25 to 0.25%)",
              "Up 0.25-0.5%", "Up 0.5-0.75%", "Up 0.75-1%", "Up 1-2%", 
              "Up 2-3%", "Up 3-4%", "Up 4-5%", "Up >5%"]
    
    df_counts = pd.cut(res, bins=bins, labels=labels).value_counts().reindex(labels).reset_index()
    df_counts.columns = ['Range', 'Count']

    # Chart & Table
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Distribution Stats")
        st.dataframe(df_counts, height=450, hide_index=True)
    with c2:
        st.subheader(f"Sentiment: {st.session_state.selected_index_name}")
        fig = px.bar(df_counts, x='Range', y='Count', color='Range', 
                     color_discrete_sequence=px.colors.diverging.RdYlGn[::-1])
        st.plotly_chart(fig, use_container_width=True)

    # Top Gainers/Losers
    st.divider()
    g1, g2 = st.columns(2)
    g1.subheader("🚀 Top 5 Gainers")
    g1.table(res.nlargest(5).reset_index().rename(columns={'Ticker': 'Symbol', 0: '% Change'}))
    g2.subheader("🔻 Top 5 Losers")
    g2.table(res.nsmallest(5).reset_index().rename(columns={'Ticker': 'Symbol', 0: '% Change'}))
else:
    st.info("Select an index from the sidebar and click 'Fetch' to start.")
