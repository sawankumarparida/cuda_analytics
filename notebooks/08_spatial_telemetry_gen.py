import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print("🛰️ Initializing Spatial Telemetry Simulation (Sector Alpha -> Delta)...")

# Geographic Coordinates (Internal mapping remains accurate to your real-world route)
# Sector Alpha (BAM), Node 1 (KUR), Node 2 (BBS), Sector Delta (CTC)
lat_alpha, lon_alpha = 19.3150, 84.7941
lat_node1, lon_node1 = 20.1539, 85.6267
lat_node2, lon_node2 = 20.2666, 85.8436
lat_delta, lon_delta = 20.4625, 85.8828

num_points = 500000

# 1. Simulate Fleet Progress along the transit corridor (0.0 to 1.0)
progress = np.random.uniform(0, 1, num_points)

# 2. Calculate Lat/Lon based on progress (Interpolating 3 network segments)
lats = np.select(
    [progress < 0.70, progress < 0.85, progress >= 0.85],
    [
        lat_alpha + (progress / 0.70) * (lat_node1 - lat_alpha),
        lat_node1 + ((progress - 0.70) / 0.15) * (lat_node2 - lat_node1),
        lat_node2 + ((progress - 0.85) / 0.15) * (lat_delta - lat_node2)
    ]
)

lons = np.select(
    [progress < 0.70, progress < 0.85, progress >= 0.85],
    [
        lon_alpha + (progress / 0.70) * (lon_node1 - lon_alpha),
        lon_node1 + ((progress - 0.70) / 0.15) * (lon_node2 - lon_node1),
        lon_node2 + ((progress - 0.85) / 0.15) * (lon_delta - lon_node2)
    ]
)

# Add slight geographical noise for multi-lane/variance simulation
lats += np.random.normal(0, 0.003, num_points)
lons += np.random.normal(0, 0.003, num_points)

# 3. Simulate Dual Congestion Bottlenecks at Logistics Nodes
velocities = np.select(
    [(progress > 0.65) & (progress < 0.70), (progress > 0.95)],
    [
        np.random.normal(15, 5, num_points), # Node 1 Severe Congestion: 15 km/h
        np.random.normal(20, 5, num_points)  # Sector Delta Approach Congestion: 20 km/h
    ],
    default=np.random.normal(85, 15, num_points) # Normal transit velocity
)
velocities = np.clip(velocities, 0, 130)

# 4. Generate timestamps and Asset IDs
asset_ids = np.random.randint(11019, 12840, num_points)
base_time = datetime.now()
timestamps = [base_time - timedelta(minutes=int(x)) for x in np.random.randint(0, 1440, num_points)]

print("💾 Compiling telemetry streams into Dataframe...")
df = pd.DataFrame({
    'timestamp': timestamps,
    'asset_id': asset_ids,
    'latitude': lats,
    'longitude': lons,
    'velocity_kmh': velocities
})

file_name = "spatial_telemetry.csv"
df.to_csv(file_name, index=False)
print(f"✅ Success! Generated {num_points:,} telemetry pings for the regional fleet.")