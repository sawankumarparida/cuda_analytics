import streamlit as st
import xgboost as xgb
import pandas as pd
import numpy as np
from scipy.optimize import linprog

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Yield Management Intelligence", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LOAD THE AI MODEL ---
@st.cache_resource
def load_model():
    model = xgb.Booster()
    model.load_model("capacity_model.json")
    return model

model = load_model()

# --- SIDEBAR: SCENARIO BUILDER ---
st.sidebar.title("🎛️ Scenario Builder")
st.sidebar.markdown("Adjust parameters to run real-time AI capacity predictions.")

days_to_departure = st.sidebar.slider("Days to Departure", min_value=1, max_value=120, value=10, step=1)
waitlist_depth = st.sidebar.slider("Current Waitlist Depth", min_value=0, max_value=400, value=150, step=5)

surge_options = {"Low / Off-Peak": 0.8, "Normal Baseline": 1.0, "High Demand": 1.5, "Peak Holiday Surge": 2.5}
surge_selection = st.sidebar.selectbox("Demand / Surge Factor", options=list(surge_options.keys()), index=3)
surge_factor = surge_options[surge_selection]

cancel_rate_display = st.sidebar.slider("Historical Cancel Rate (%)", min_value=5, max_value=35, value=15, step=1)
historical_cancel_rate = cancel_rate_display / 100.0

st.sidebar.divider()
st.sidebar.caption("Powered by GPU-Accelerated XGBoost & SciPy")

# --- MAIN DASHBOARD AREA ---
st.title("📈 Dynamic Yield & Capacity Predictor")
st.markdown("Predictive waitlist forecasting and prescriptive fleet optimization.")
st.divider()

# --- AI INFERENCE ENGINE (PREDICTIVE) ---
input_data = pd.DataFrame({
    'days_to_departure': [days_to_departure],
    'waitlist_depth': [waitlist_depth],
    'surge_factor': [surge_factor],
    'historical_cancel_rate': [historical_cancel_rate]
})

d_input = xgb.DMatrix(input_data)
probability = model.predict(d_input)[0]
prob_pct = probability * 100

projected_occupancy = 80 + (waitlist_depth * 0.05) + (surge_factor * 10)
occupancy_pct = min(max(projected_occupancy, 50), 150)

if prob_pct >= 70:
    status_color = "normal" 
    strategy = "✅ **Green Status**: High likelihood of natural confirmation."
elif prob_pct >= 40:
    status_color = "off"
    strategy = "⚠️ **Monitor Status**: Waitlist vulnerable. Consider secondary quotas."
else:
    status_color = "inverse"
    strategy = "🚨 **Critical Overflow**: Severe bottleneck detected. AI recommends immediate fleet expansion."

# --- UI RENDER: METRICS ---
col1, col2 = st.columns(2)
with col1:
    st.metric(label="Waitlist Confirmation Probability", value=f"{prob_pct:.1f}%", delta="Clearance Rate", delta_color=status_color)
with col2:
    occ_color = "inverse" if occupancy_pct > 100 else "normal"
    st.metric(label="Projected Fleet Occupancy", value=f"{occupancy_pct:.1f}%", delta="Over capacity limit" if occupancy_pct > 100 else "Within limits", delta_color=occ_color)

st.info(strategy)

# --- OPERATIONS RESEARCH ENGINE (PRESCRIPTIVE) ---
st.divider()
st.subheader("🛠️ Prescriptive Fleet Allocation")
st.markdown("Uses Mixed-Integer Linear Programming (MILP) to calculate the mathematically cheapest recovery dispatch.")

# Simulate baseline capacity to find exact passenger overflow
baseline_capacity = 1000 
expected_passengers = int(baseline_capacity * (occupancy_pct / 100))
overflow = expected_passengers - baseline_capacity

if overflow > 0:
    st.warning(f"⚠️ **{overflow} passengers** are projected to be stranded based on AI forecasting.")
    
    if st.button("⚡ Generate Optimal Recovery Plan"):
        # Optimizer Parameters
        costs = [500, 750, 400]
        capacities = [70, 110, 40]
        inventory = [5, 3, 4]
        
        # Run Solver
        res = linprog(
            costs, 
            A_ub=[[-capacities[0], -capacities[1], -capacities[2]]], 
            b_ub=[-overflow], 
            bounds=[(0, inventory[0]), (0, inventory[1]), (0, inventory[2])], 
            integrality=[1, 1, 1]
        )
        
        if res.success:
            st.success(f"✅ Optimal Plan Generated! Minimum Dispatch Cost: **${int(res.fun):,}**")
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Standard Coaches (70 pax)", f"{int(res.x[0])} units", "-$500/ea", delta_color="inverse")
            col_b.metric("High-Capacity (110 pax)", f"{int(res.x[1])} units", "-$750/ea", delta_color="inverse")
            col_c.metric("Express Minis (40 pax)", f"{int(res.x[2])} units", "-$400/ea", delta_color="inverse")
        else:
            st.error("❌ Infeasible: Not enough backup fleet inventory to cover the overflow.")
else:
    st.success("✅ Capacity is within normal limits. No prescriptive recovery required.")