import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# Page configuration for a pro quant terminal look
st.set_page_config(page_title="Live Crypto Quant Terminal", layout="wide")

# Safe auto-refresh interval (set to 60 seconds to prevent thread/memory overload)
st_autorefresh(interval=60000, key="crypto_refresh")

st.title("⚡ Live Crypto Quant Terminal")
st.markdown("Real-time multi-asset market data pipeline with Quantitative Moving Averages (EMA/SMA).")

# Point Streamlit to the Linux mount path in WSL
DB_PATH = "/mnt/c/Users/skpar/Downloads/live_market_data.db"

@st.cache_data(ttl=15)
def load_data():
    try:
        # Use context manager to safely open and close the SQLite connection
        with sqlite3.connect(DB_PATH) as conn:
            query = "SELECT * FROM crypto_prices ORDER BY Datetime ASC"
            df = pd.read_sql(query, conn)
            
        if not df.empty:
            df["Datetime"] = pd.to_datetime(df["Datetime"])
        return df
    except Exception as e:
        # Gracefully handle missing table or file lock errors instead of crashing
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("Waiting for data... Make sure your Python background daemon (`05_powerbi_daemon.py`) is running and writing rows to the database!")
else:
    # Sidebar filters / Controls
    st.sidebar.header("Terminal Controls")
    available_assets = df["Asset"].unique().tolist()
    selected_assets = st.sidebar.multiselect(
        "Select Assets", 
        options=available_assets, 
        default=available_assets
    )
    
    # Filter dataframe based on sidebar selection
    filtered_df = df[df["Asset"].isin(selected_assets)].copy()

    # Calculate Quantitative Indicators (Fast EMA 5 & Slow SMA 20 per Asset)
    if not filtered_df.empty:
        filtered_df['EMA_5'] = filtered_df.groupby('Asset')['Price_USD'].transform(lambda x: x.ewm(span=5).mean())
        filtered_df['SMA_20'] = filtered_df.groupby('Asset')['Price_USD'].transform(lambda x: x.rolling(window=20).mean())

    # Main Multi-Line Price Chart with Moving Averages
    st.subheader("Live Price Action & Quantitative Indicators (USD)")
    if not filtered_df.empty:
        # We plot the raw price action first
        fig = px.line(
            filtered_df, 
            x="Datetime", 
            y="Price_USD", 
            color="Asset",
            markers=True,
            template="plotly_dark"
        )
        
        # Overlay EMA and SMA lines dynamically for each asset
        for asset in selected_assets:
            asset_df = filtered_df[filtered_df['Asset'] == asset]
            if not asset_df.empty:
                fig.add_trace(
                    px.line(asset_df, x="Datetime", y="EMA_5").update_traces(line=dict(dash="dot")).data[0]
                )
                fig.add_trace(
                    px.line(asset_df, x="Datetime", y="SMA_20").update_traces(line=dict(dash="dash")).data[0]
                )

        fig.update_layout(
            xaxis_title="Timestamp (UTC)",
            yaxis_title="Price / Indicator Value (USD)",
            hovermode="x unified"
        )
        st.plotly_chart(fig, width='stretch')

    # Display live pipeline metrics at the bottom
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Pipeline Rows", len(df))
    col2.metric("Tracked Assets", len(available_assets))
    col3.metric("Last Updated", str(df["Datetime"].max()) if not df.empty else "N/A")

    # Raw Data Inspector
    with st.expander("View Raw Database Logs & Indicators"):
        st.dataframe(filtered_df.tail(20), width='stretch')