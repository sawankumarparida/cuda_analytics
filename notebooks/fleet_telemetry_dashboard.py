import streamlit as st
import streamlit.components.v1 as components

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Spatial Logistics Telemetry", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SIDEBAR METRICS ---
st.sidebar.title("🛰️ Fleet Control Center")
st.sidebar.markdown("Real-time GPU-accelerated congestion monitoring across the regional transit corridor.")
st.sidebar.divider()

st.sidebar.subheader("Live Network Status")
st.sidebar.metric(label="Active Assets in Transit", value="4,102", delta="124 Active")
st.sidebar.metric(label="Average Fleet Velocity", value="68 km/h", delta="-12 km/h", delta_color="inverse")
st.sidebar.metric(label="Detected Severe Bottlenecks", value="2", delta="Node 1, Sector Delta", delta_color="inverse")

st.sidebar.divider()
st.sidebar.info(
    "**Architecture:**\n\n"
    "• **Hardware:** NVIDIA RTX 3050 Ti\n"
    "• **Engine:** RAPIDS cuDF (CUDA)\n"
    "• **Visualization:** WebGL (Kepler.gl)\n"
    "• **Points Rendered:** 500,000"
)

# --- MAIN DASHBOARD AREA ---
st.title("🚛 Regional Fleet Spatial Telemetry")
st.markdown("Visualizing 500,000 telemetry pings to identify spatial bottlenecks and velocity degradation.")

# --- RENDER THE KEPLER MAP ---
# Open the HTML file saved from Jupyter and inject it into Streamlit
try:
    with open("fleet_telemetry_dashboard.html", "r", encoding="utf-8") as f:
        html_map = f.read()
    
    # Display the HTML string in an iframe
    components.html(html_map, height=750, scrolling=False)
except FileNotFoundError:
    st.error("Error: 'fleet_telemetry_dashboard.html' not found. Please ensure you saved the map from Jupyter Notebook first.")

st.caption("Hover over points to see individual asset velocity. Use the timeline filter in the map to animate historical movement.")