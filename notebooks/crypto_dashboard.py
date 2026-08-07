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
st.markdown("Real-time multi-asset market data pipeline powered by Python, SQLite, and Streamlit.")

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
    filtered_df = df[df["Asset"].isin(selected_assets)]

    # Main Multi-Line Price Chart (Updated with new width='stretch' syntax)
    st.subheader("Live Price Action (USD)")
    if not filtered_df.empty:
        fig = px.line(
            filtered_df, 
            x="Datetime", 
            y="Price_USD", 
            color="Asset",
            markers=True,
            template="plotly_dark"
        )
        fig.update_layout(
            xaxis_title="Timestamp (UTC)",
            yaxis_title="Price (USD)",
            legend_title="Asset",
            hovermode="x unified"
        )
        st.plotly_chart(fig, width='stretch')

    # Display live pipeline metrics at the bottom
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Pipeline Rows", len(df))
    col2.metric("Tracked Assets", len(available_assets))
    col3.metric("Last Updated", str(df["Datetime"].max()) if not df.empty else "N/A")

    # Raw Data Inspector (Updated with new width='stretch' syntax)
    with st.expander("View Raw Database Logs"):
        st.dataframe(df.tail(20), width='stretch')