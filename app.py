import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import logging

# Silence logs
yf.utils.get_yf_logger().setLevel(logging.CRITICAL)

st.set_page_config(page_title="Indian Market Breadth", layout="wide")

# 1. Index Configuration
INDICES = {
    "Nifty 50": "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
    "Nifty Next 50": "https://archives.nseindia.com/content/indices/ind_niftynext50list.csv",
    "Nifty 100": "https://archives.nseindia.com/content/indices/ind_nifty100list.csv",
    "Nifty 200": "https://archives.nseindia.com/content/indices/ind_nifty200list.csv",
    "Nifty 500": "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
    "Nifty Bank": "https://archives.nseindia.com/content/indices/ind_niftybanklist.csv",
    "Nifty IT": "https://archives.nseindia.com/content/indices/ind_niftyitlist.csv",
    "Nifty FMCG": "https://archives.nseindia.com/content/indices/ind_niftyfmcglist.csv",
}

st.title("🇮🇳 Indian Market Advance-Decline Dashboard")

# 2. UI Sidebar for Settings
with st.sidebar:
    st.header("Settings")
    selected_index = st.selectbox("Select Index", list(INDICES.keys()))
    refresh = st.button("Fetch Latest Data")

# 3. Processing Logic
if refresh:
    with st.spinner(f"Downloading data for {selected_index}..."):
        # Load tickers
        df_list = pd.read_csv(INDICES[selected_index])
        tickers = [s + ".NS" for s in df_list['Symbol'] if "DUMMY" not in str(s)]
        
        # Download Data
        data = yf.download(tickers, period="2d", interval="1d", progress=False, auto_adjust=True)
        if data.empty:
            st.error("No data found. Market might be closed or API limit reached.")
        else:
            pct_change = data['Close'].pct_change().iloc[-1] * 100
            pct_change = pct_change.dropna()

            # 4. Define Granular Bins (0.25, 0.5, 0.75, 1, 2, 3, 4, 5)
            bins = [-100, -5, -4, -3, -2, -1, -0.75, -0.5, -0.25, 0.25, 0.5, 0.75, 1, 2, 3, 4, 5, 100]
            labels = [
                "Down >5%", "Down 4-5%", "Down 3-4%", "Down 2-3%", "Down 1-2%", 
                "Down 0.75-1%", "Down 0.5-0.75%", "Down 0.25-0.5%", "Flat (-0.25 to 0.25%)",
                "Up 0.25-0.5%", "Up 0.5-0.75%", "Up 0.75-1%", "Up 1-2%", 
                "Up 2-3%", "Up 3-4%", "Up 4-5%", "Up >5%"
            ]
            
            # The 'bins' has 18 edges, so it needs 17 labels.
            # We use pd.cut to categorize every stock
            df_counts = pd.cut(pct_change, bins=bins, labels=labels).value_counts().reindex(labels).reset_index()
            df_counts.columns = ['Range', 'Count']

            # 5. Display Results
            col1, col2 = st.columns([1, 2])
            with col1:
                st.subheader("Data Summary")
                st.dataframe(df_counts, height=600, hide_index=True)
            
            with col2:
                st.subheader("Visual Distribution")
                # Color code: Red for down, Grey for flat, Green for up
                fig = px.bar(df_counts, x='Range', y='Count', color='Range',
                             color_discrete_sequence=px.colors.diverging.RdYlGn[::-1])
                st.plotly_chart(fig, use_container_width=True)
                
            st.success(f"Successfully analyzed {len(pct_change)} stocks in {selected_index}.")
