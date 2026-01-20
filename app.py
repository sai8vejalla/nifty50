import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import logging

# 1. Setup & Session State
yf.utils.get_yf_logger().setLevel(logging.CRITICAL)
st.set_page_config(page_title="Nifty Breadth", layout="wide")

if 'market_data' not in st.session_state:
    st.session_state.market_data = None

INDICES = {
    "Nifty 50": "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
    "Nifty 500": "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
    "Nifty Bank": "https://archives.nseindia.com/content/indices/ind_niftybanklist.csv",
}

st.title("🇮🇳 Indian Market Advance-Decline")

# 2. Sidebar
selected_index = st.sidebar.selectbox("Select Index", list(INDICES.keys()))
if st.sidebar.button("Fetch Latest Data"):
    with st.spinner("Downloading..."):
        try:
            df_list = pd.read_csv(INDICES[selected_index])
            tickers = [s + ".NS" for s in df_list['Symbol'] if "DUMMY" not in str(s)]
            
            # Download
            data = yf.download(tickers, period="2d", interval="1d", progress=False, auto_adjust=True)
            
            if not data.empty:
                # Calculate change and store in session state
                change = data['Close'].pct_change().iloc[-1] * 100
                st.session_state.market_data = change.dropna()
                st.success(f"Data Loaded for {len(tickers)} stocks!")
            else:
                st.error("Yahoo Finance returned no data. Try again in a minute.")
        except Exception as e:
            st.error(f"Error: {e}")

# 3. Display Data (Persistent)
if st.session_state.market_data is not None:
    pct_change = st.session_state.market_data
    
    # Define Bins
    bins = [-100, -5, -4, -3, -2, -1, -0.75, -0.5, -0.25, 0.25, 0.5, 0.75, 1, 2, 3, 4, 5, 100]
    labels = ["Down >5%", "Down 4-5%", "Down 3-4%", "Down 2-3%", "Down 1-2%", 
              "Down 0.75-1%", "Down 0.5-0.75%", "Down 0.25-0.5%", "Flat",
              "Up 0.25-0.5%", "Up 0.5-0.75%", "Up 0.75-1%", "Up 1-2%", 
              "Up 2-3%", "Up 3-4%", "Up 4-5%", "Up >5%"]
    
    df_counts = pd.cut(pct_change, bins=bins, labels=labels).value_counts().reindex(labels).reset_index()
    df_counts.columns = ['Range', 'Count']

    # Visuals
    c1, c2 = st.columns([1, 2])
    c1.dataframe(df_counts, height=450)
    fig = px.bar(df_counts, x='Range', y='Count', color='Range', 
                 color_discrete_sequence=px.colors.diverging.RdYlGn[::-1])
    c2.plotly_chart(fig, use_container_width=True)
else:
    st.info("👈 Select an index and click 'Fetch Latest Data' in the sidebar to begin.")
