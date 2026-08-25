import numpy as np
from scipy.optimize import linprog

print("🧮 Initializing Fleet Allocation Optimizer...")

# --- 1. THE PARAMETERS ---
# Fleet Types: [Standard Coach, High-Capacity, Express Mini]
costs = [500, 750, 400]        # Cost to dispatch each vehicle type ($)
capacities = [70, 110, 40]     # Passenger capacity per vehicle type
inventory = [5, 3, 4]          # Maximum available units of each type

target_demand = 500            # The stranded passenger waitlist we must clear

# --- 2. SETTING UP THE LINEAR PROGRAM ---
# SciPy linprog strictly minimizes, so our objective array (costs) is perfect.
c = costs

# SciPy linprog uses "Less Than or Equal To" (<=) for constraints.
# We need Capacity >= Target. 
# Multiplying by -1 flips it to: -Capacity <= -Target.
A_ub = [[-capacities[0], -capacities[1], -capacities[2]]]
b_ub = [-target_demand]

# Define the inventory limits for each fleet type (0 to max available)
bounds = [
    (0, inventory[0]), 
    (0, inventory[1]), 
    (0, inventory[2])
]

# Force the solver to output whole numbers (can't send half a vehicle)
# 1 = Integer variable
integrality = [1, 1, 1]

print(f"🚨 Target: Clear {target_demand} passengers at minimal cost.")
print("⚙️ Running Mixed-Integer Linear Programming (MILP) Solver...\n")

# --- 3. RUN THE SOLVER ---
result = linprog(
    c, 
    A_ub=A_ub, 
    b_ub=b_ub, 
    bounds=bounds, 
    integrality=integrality
)

# --- 4. OUTPUT THE OPTIMAL BUSINESS DECISION ---
if result.success:
    print("✅ OPTIMAL STRATEGY FOUND:")
    print("-" * 30)
    print(f"Standard Coaches (Capacity 70, Cost $500)   : {int(result.x[0])} units")
    print(f"High-Capacity    (Capacity 110, Cost $750)  : {int(result.x[1])} units")
    print(f"Express Minis    (Capacity 40, Cost $400)   : {int(result.x[2])} units")
    print("-" * 30)
    
    total_capacity = (result.x[0]*capacities[0]) + (result.x[1]*capacities[1]) + (result.x[2]*capacities[2])
    print(f"📊 Total Passengers Accommodated : {int(total_capacity)}")
    print(f"💰 Minimum Total Dispatch Cost   : ${int(result.fun):,}")
else:
    print("❌ INFEASIBLE: Not enough total fleet inventory to clear the demand.")