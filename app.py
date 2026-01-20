import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import logging

# 1. Setup & Configuration
yf.utils.get_yf_logger().setLevel(logging.CRITICAL)
st.set_page_config(page_title="Indian Market Analyzer", layout="wide")

if 'data_cache' not in st.session_state:
    st.session_state.data_cache = None

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
st.markdown("Analyze the distribution of returns and relative strength across major NSE indices.")

# 2. Sidebar Controls
with st.sidebar:
    st.header("Settings")
    selected_index = st.selectbox("Select Index", list(INDICES.keys()), index=0)
    benchmark = st.selectbox("Benchmark for RS", ["^NSEI", "^NSEBANK"], help="^NSEI is Nifty 50, ^NSEBANK is Bank Nifty")
    fetch_btn = st.button("Run Analysis", type="primary")

# 3. Data Processing Logic
if fetch_btn:
    with st.spinner(f"Fetching data for {selected_index}..."):
        try:
            # Load Tickers
            df_list = pd.read_csv(INDICES[selected_index])
            tickers = [s.strip() + ".NS" for s in df_list['Symbol'] if "DUMMY" not in str(s)]
            
            # Download Data (5 days to ensure we have at least 2 valid closing days for pct_change)
            all_tickers = tickers + [benchmark]
            raw_data = yf.download(all_tickers, period="5d", interval="1d", progress=False)['Close']
            
            # Absolute % Change (Last available session)
            abs_change = raw_data[tickers].pct_change().iloc[-1] * 100
            
            # Relative Strength % Change
            # RS Ratio = Stock Price / Benchmark Price
            rs_ratio = raw_data[tickers].div(raw_data[benchmark], axis=0)
            rs_change = rs_ratio.pct_change().iloc[-1] * 100
            
            st.session_state.data_cache = {
                "abs": abs_change.dropna(),
                "rs": rs_change.dropna(),
                "index_name": selected_index,
                "bench_name": benchmark
            }
        except Exception as e:
            st.error(f"Error fetching data: {e}")

# 4. Visualization & Reporting
if st.session_state.data_cache:
    cache = st.session_state.data_cache
    
    # Define Bins and Labels
    bins = [-100, -5, -4, -3, -2, -1, -0.75, -0.5, -0.25, 0.25, 0.5, 0.75, 1, 2, 3, 4, 5, 100]
    labels = ["<-5%", "-4%", "-3%", "-2%", "-1%", "-0.75%", "-0.5%", "-0.25%", "Flat", 
              "0.25%", "0.5%", "0.75%", "1%", "2%", "3%", "4%", ">5%"]

    def create_distribution_df(series):
        counts = pd.cut(series, bins=bins, labels=labels).value_counts().reindex(labels).reset_index()
        counts.columns = ['Range', 'Count']
        return counts

    # Generate Chart Data
    df_abs = create_distribution_df(cache['abs'])
    df_rs = create_distribution_df(cache['rs'])

    # UI Columns for Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"📊 {cache['index_name']} Breadth (Abs %)")
        fig_abs = px.bar(df_abs, x='Range', y='Count', color='Range', text_auto=True,
                         color_discrete_sequence=px.colors.diverging.RdYlGn[::-1])
        fig_abs.update_layout(showlegend=False, xaxis_title="Return Range", yaxis_title="Number of Stocks")
        st.plotly_chart(fig_abs, use_container_width=True)

    with col2:
        st.subheader(f"💪 RS vs {cache['bench_name']}")
        fig_rs = px.bar(df_rs, x='Range', y='Count', color='Range', text_auto=True,
                        color_discrete_sequence=px.colors.diverging.Spectral)
        fig_rs.update_layout(showlegend=False, xaxis_title="RS Change Range", yaxis_title="Number of Stocks")
        st.plotly_chart(fig_rs, use_container_width=True)
    
    # 5. Summary Table with Percentages
    st.divider()
    st.subheader("📋 Market Distribution Summary")
    
    # Prepare DataFrame
    summary_df = df_abs.rename(columns={'Count': 'Abs Count'})
    summary_df['RS Count'] = df_rs['Count']
    
    # Calculate Percentages
    total_stocks = summary_df['Abs Count'].sum()
    summary_df['Abs %'] = (summary_df['Abs Count'] / total_stocks * 100)
    summary_df['RS %'] = (summary_df['RS Count'] / total_stocks * 100)
    
    # Reorder for clarity
    summary_df = summary_df[['Range', 'Abs Count', 'Abs %', 'RS Count', 'RS %']]
    
    # Display styled table
    st.table(summary_df.style.format({
        'Abs %': '{:.2f}%',
        'RS %': '{:.2f}%'
    }))

    # Quick Stats
    advances = (cache['abs'] > 0).sum()
    declines = (cache['abs'] < 0).sum()
    st.info(f"**Quick Stats:** {advances} Advances | {declines} Declines | Ratio: {round(advances/max(declines,1), 2)}")
else:
    st.info("Select an index from the sidebar and click 'Run Analysis' to begin.")
