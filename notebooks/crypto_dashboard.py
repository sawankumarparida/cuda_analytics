import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# Page configuration for a pro quant terminal look
st.set_page_config(page_title="Live Crypto Quant Terminal", layout="wide")

# Auto-refresh the dashboard every 30 seconds to fetch new data from SQLite
st_autorefresh(interval=30000, key="crypto_refresh")

st.title("⚡ Live Crypto Quant Terminal")
st.markdown("Real-time multi-asset market data pipeline powered by Python, SQLite, and Streamlit.")

# Connect to your SQLite database located in your Windows Downloads folder
DB_PATH = r"C:\Users\skpar\Downloads\live_market_data.db"

@st.cache_data(ttl=10)
def load_data():
    try:
        conn = sqlite3.connect(DB_PATH)
        query = "SELECT * FROM crypto_prices ORDER BY Datetime ASC"
        df = pd.read_sql(query, conn)
        conn.close()
        # Ensure Datetime column is parsed correctly as datetime objects
        df["Datetime"] = pd.to_datetime(df["Datetime"])
        return df
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("Waiting for data... Make sure your Python background daemon (`05_powerbi_daemon.py`) is running and writing rows to the database!")
else:
    # Sidebar filters / Controls
    st.sidebar.header("Terminal Controls")
    selected_assets = st.sidebar.multiselect(
        "Select Assets", 
        options=df["Asset"].unique(), 
        default=df["Asset"].unique()
    )
    
    # Filter dataframe based on sidebar selection
    filtered_df = df[df["Asset"].isin(selected_assets)]

    # Main Multi-Line Price Chart
    st.subheader("Live Price Action (USD)")
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
    st.plotly_chart(fig, use_container_width=True)

    # Display live pipeline metrics at the bottom
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Pipeline Rows", len(df))
    col2.metric("Tracked Assets", len(df["Asset"].unique()))
    col3.metric("Last Updated", str(df["Datetime"].max()))

    # Raw Data Inspector
    with st.expander("View Raw Database Logs"):
        st.dataframe(df.tail(20), use_container_width=True)