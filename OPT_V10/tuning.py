from gurobipy import read, GRB
import time
import csv
from itertools import product

# Define your parameter grid or combinations
parameter_grid = {
    "Method": [0, 1, 2],  # 0: Dual Simplex, 1: Primal Simplex, 2: Barrier
    "Presolve": [0, 1, 2],  # 0: None, 1: Conservative, 2: Aggressive
    "Cuts": [0, 1, 2],  # 0: None, 1: Low, 2: High
    "Heuristics": [0.05, 0.4, 0.7],
    "ScaleFlag": [0, 2]  # 0: OFF, 2: Geometric scaling
}

# Generate all combinations of parameters
combinations = list(product(*parameter_grid.values()))

# Function to load the model
def load_model():
    model = read("model.lp")
    model.setParam('MIPGap', 0.001)
    model.setParam('NumericFocus', 3)
    model.setParam('TimeLimit', 10)
    model.setParam('IntegralityFocus', 1)
    return model

# Prepare CSV file for results
csv_filename = "optimization_results.csv"
with open(csv_filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    header = list(parameter_grid.keys()) + ["Objective Value", "Solve Time (s)", "Optimality Gap"]
    writer.writerow(header)

    # Test each parameter combination
    for comb in combinations:
        model = load_model()
        
        # Set parameters dynamically
        for param, value in zip(parameter_grid.keys(), comb):
            model.setParam(param, value)
        
        # Optimize the model
        start_time = time.time()
        model.optimize()
        end_time = time.time()
        
        solve_time = end_time - start_time
        
        # Collect results if optimization was successful
        if model.status == GRB.OPTIMAL or model.status == GRB.SUBOPTIMAL:
            obj_value = model.objVal
            gap = model.MIPGap if model.status == GRB.OPTIMAL else "N/A"
            
            result_row = list(comb) + [obj_value, solve_time, gap]
            writer.writerow(result_row)
            
            print(f"Tested Params: {dict(zip(parameter_grid.keys(), comb))}, Objective Value: {obj_value}, Solve Time: {solve_time:.2f} s, Gap: {gap}")

print(f"Results saved to {csv_filename}")
