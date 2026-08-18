import pandas as pd
import numpy as np

print("📊 Initializing 1,000,000 historical booking records...")
num_records = 1000000

# 1. Generate core features (The inputs)
days_to_departure = np.random.randint(1, 120, num_records)
waitlist_depth = np.random.randint(1, 400, num_records)
# 1.0 is normal demand, 2.5 is peak holiday surge (Diwali/Dussehara)
surge_factor = np.random.uniform(0.5, 2.5, num_records) 
historical_cancel_rate = np.random.uniform(0.05, 0.35, num_records)

# 2. Simulate the hidden Confirmation Logic 
# Higher days to departure & higher cancel rates = Better chance
# Higher waitlist & high surge = Worse chance
prob = (days_to_departure * 0.5) - (waitlist_depth * 0.4) - (surge_factor * 20) + (historical_cancel_rate * 100) + 50
prob += np.random.normal(0, 15, num_records) # Add real-world randomness
prob = np.clip(prob, 5, 95)

# Convert mathematical probability to 1 (Confirmed) or 0 (Waitlisted)
is_confirmed = (np.random.uniform(0, 100, num_records) < prob).astype(int)

# 3. Calculate final occupancy percentage (Target B)
occupancy = 80 + (waitlist_depth * 0.05) + (surge_factor * 10) + np.random.normal(0, 5, num_records)
occupancy = np.clip(occupancy, 50, 150).round(1)

print("💾 Compiling dataset...")
df = pd.DataFrame({
    'days_to_departure': days_to_departure,
    'waitlist_depth': waitlist_depth,
    'surge_factor': surge_factor.round(2),
    'historical_cancel_rate': historical_cancel_rate.round(2),
    'is_confirmed': is_confirmed,
    'final_occupancy_pct': occupancy
})

file_name = "booking_capacity_data.csv"
df.to_csv(file_name, index=False)
print(f"✅ Success! Saved 1 Million records to '{file_name}'.")