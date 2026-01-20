# 5. Visualization with Labels
if st.session_state.data_cache:
    cache = st.session_state.data_cache
    
    bins = [-100, -5, -4, -3, -2, -1, -0.75, -0.5, -0.25, 0.25, 0.5, 0.75, 1, 2, 3, 4, 5, 100]
    labels = ["<-5%", "-4%", "-3%", "-2%", "-1%", "-0.75%", "-0.5%", "-0.25%", "Flat", 
              "0.25%", "0.5%", "0.75%", "1%", "2%", "3%", "4%", ">5%"]

    def create_distribution_df(series):
        counts = pd.cut(series, bins=bins, labels=labels).value_counts().reindex(labels).reset_index()
        counts.columns = ['Range', 'Count']
        return counts

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"📊 {cache['index_name']} Breadth")
        df_abs = create_distribution_df(cache['abs'])
        fig_abs = px.bar(df_abs, x='Range', y='Count', color='Range', text_auto=True,
                         color_discrete_sequence=px.colors.diverging.RdYlGn[::-1])
        st.plotly_chart(fig_abs, use_container_width=True)

    with col2:
        st.subheader(f"💪 RS vs {cache['bench_name']}")
        df_rs = create_distribution_df(cache['rs'])
        fig_rs = px.bar(df_rs, x='Range', y='Count', color='Range', text_auto=True,
                        color_discrete_sequence=px.colors.diverging.Spectral)
        st.plotly_chart(fig_rs, use_container_width=True)
    
    # --- UPDATED SUMMARY TABLE LOGIC ---
    st.divider()
    st.subheader("📋 Category Summary & Market Weight")
    
    # Merge the dataframes
    summary_df = df_abs.rename(columns={'Count': 'Abs Count'})
    summary_df['RS Count'] = df_rs['Count']
    
    # Calculate Percentages
    total_stocks = summary_df['Abs Count'].sum()
    
    summary_df['Abs %'] = (summary_df['Abs Count'] / total_stocks * 100).round(2)
    summary_df['RS %'] = (summary_df['RS Count'] / total_stocks * 100).round(2)
    
    # Reorder columns for better readability
    summary_df = summary_df[['Range', 'Abs Count', 'Abs %', 'RS Count', 'RS %']]
    
    # Format the % columns to show the percent sign
    styled_df = summary_df.style.format({
        'Abs %': '{:.2f}%',
        'RS %': '{:.2f}%'
    })
    
    st.table(styled_df) 
