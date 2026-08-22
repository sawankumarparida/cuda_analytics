import streamlit as st
import xgboost as xgb
import pandas as pd
import numpy as np

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Yield Management Intelligence", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LOAD THE AI MODEL ---
# We use @st.cache_resource so it only loads the model once, making the app lightning fast
@st.cache_resource
def load_model():
    model = xgb.Booster()
    model.load_model("capacity_model.json")
    return model

model = load_model()

# --- SIDEBAR: SCENARIO BUILDER ---
st.sidebar.title("🎛️ Scenario Builder")
st.sidebar.markdown("Adjust the parameters below to run real-time AI capacity predictions.")

days_to_departure = st.sidebar.slider("Days to Departure", min_value=1, max_value=120, value=30, step=1)
waitlist_depth = st.sidebar.slider("Current Waitlist Depth", min_value=0, max_value=400, value=50, step=5)

surge_options = {"Low / Off-Peak": 0.8, "Normal Baseline": 1.0, "High Demand": 1.5, "Peak Holiday Surge": 2.5}
surge_selection = st.sidebar.selectbox("Demand / Surge Factor", options=list(surge_options.keys()), index=1)
surge_factor = surge_options[surge_selection]

cancel_rate_display = st.sidebar.slider("Historical Cancel Rate (%)", min_value=5, max_value=35, value=15, step=1)
historical_cancel_rate = cancel_rate_display / 100.0

st.sidebar.divider()
st.sidebar.caption("Powered by GPU-Accelerated XGBoost")

# --- MAIN DASHBOARD AREA ---
st.title("📈 Dynamic Yield & Capacity Predictor")
st.markdown("Predictive waitlist confirmation forecasting for proactive capacity management.")
st.divider()

# --- AI INFERENCE ENGINE ---
# Package the UI inputs exactly how the model expects them
input_data = pd.DataFrame({
    'days_to_departure': [days_to_departure],
    'waitlist_depth': [waitlist_depth],
    'surge_factor': [surge_factor],
    'historical_cancel_rate': [historical_cancel_rate]
})

# Run the prediction
d_input = xgb.DMatrix(input_data)
probability = model.predict(d_input)[0]
prob_pct = probability * 100

# --- CALCULATE BUSINESS METRICS ---
# Calculate a deterministic Projected Occupancy based on the inputs
projected_occupancy = 80 + (waitlist_depth * 0.05) + (surge_factor * 10)
occupancy_pct = min(max(projected_occupancy, 50), 150)

# Determine Color and Risk Strategy based on AI Probability
if prob_pct >= 70:
    status_color = "normal" 
    strategy = "✅ **Green Status**: High likelihood of natural confirmation. No immediate capacity expansion required."
elif prob_pct >= 40:
    status_color = "off"
    strategy = "⚠️ **Monitor Status**: Waitlist is vulnerable to remaining unconfirmed. Consider opening secondary quotas."
else:
    status_color = "inverse"
    strategy = "🚨 **Critical Overflow**: Severe bottleneck detected. Highly recommend attaching additional fleet capacity."

# --- UI RENDER: METRICS ---
col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="Waitlist Confirmation Probability", 
        value=f"{prob_pct:.1f}%", 
        delta="Clearance Rate",
        delta_color=status_color
    )
    
with col2:
    # If occupancy goes over 100%, show it in red (inverse)
    occ_color = "inverse" if occupancy_pct > 100 else "normal"
    st.metric(
        label="Projected Fleet Occupancy", 
        value=f"{occupancy_pct:.1f}%", 
        delta="Over capacity limit" if occupancy_pct > 100 else "Within safety limits",
        delta_color=occ_color
    )

st.divider()

# --- UI RENDER: INSIGHTS ---
st.subheader("Automated Strategy Recommendation")
st.info(strategy)

# Show the raw data table for transparency
with st.expander("View Raw Inference Payload"):
    st.dataframe(input_data, use_container_width=True)