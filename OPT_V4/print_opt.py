import pandas as pd

def export_optimal_values(model, filename="optimal_solution.csv"):
    data = []
    
    # Extract single-dimension variables
    single_vars = {
        "C_cond": model.C_cond,
        "C_subs": model.C_subs,
    }
    
    for var_name, var in single_vars.items():
        data.append([var_name, ""] + [""] + [var.value])
    
    # Extract indexed variables
    indexed_vars = {
        "C_losses": model.C_losses,
        "subs_hv_capacity": model.subs_hv_capacity,
        "subs_mv_capacity": model.subs_mv_capacity,
        "phi": model.phi,
    }
    
    for var_name, var in indexed_vars.items():
        for index in var:
            data.append([var_name, index, ""] + [var[index].value])
    
    # Extract binary and indexed variables with multiple indices
    multi_indexed_vars = {
        "line_opt": model.line_opt,
        "line_act": model.line_act,
        "subs_hv_S": model.subs_hv_S,
        "subs_hv_P": model.subs_hv_P,
        "subs_hv_Q": model.subs_hv_Q,
        "beta": model.beta,
        "subs_mv_S": model.subs_mv_S,
        "gamma": model.gamma,
        "current_squared_k": model.current_squared_k,
        "current_squared": model.current_squared,
        "current_slack": model.current_slack,
        "active_power_k": model.active_power_k,
        "active_power": model.active_power,
        "reactive_power_k": model.reactive_power_k,
        "reactive_power": model.reactive_power,
        "voltage_squared": model.voltage_squared,
    }
    
    max_indices = 0  # Track the maximum number of indices
    
    for var_name, var in multi_indexed_vars.items():
        for index in var:
            # Ensure index is always a tuple
            index_tuple = index if isinstance(index, tuple) else (index,)
            max_indices = max(max_indices, len(index_tuple))  # Track max number of indices
            
            data.append([var_name] + list(index_tuple) + [var[index].value])

    # Ensure all rows have the same number of columns
    for i in range(len(data)):
        while len(data[i]) < (2 + max_indices):  # Adjust to max indices count
            data[i].insert(2, "")  # Insert empty string for missing index values

    # Create column headers dynamically
    index_columns = [f"Index{i+1}" for i in range(max_indices)]
    columns = ["Variable"] + index_columns + ["Value"]
    
    # Create DataFrame and export to CSV
    df = pd.DataFrame(data, columns=columns)
    df.to_csv(filename, index=False)
    
    print(f"Optimal solution exported to {filename}")

# Example usage (assuming the model is solved)
# export_optimal_values(model)
