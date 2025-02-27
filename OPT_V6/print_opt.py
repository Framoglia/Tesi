import pandas as pd
from pyomo.core import Var

def export_optimal_values(model, filename="optimal_solution.csv"):
    data = []
    max_indices = 0  # Track max index depth

    # Loop through all variables in the model
    for var_name in model.component_objects(Var, active=True):
        var_object = getattr(model, var_name.local_name)
        
        for index in var_object:
            value = var_object[index].value
            
            # Ensure index is always a tuple
            index_tuple = index if isinstance(index, tuple) else (index,)
            max_indices = max(max_indices, len(index_tuple))
            
            data.append([var_name.local_name] + list(index_tuple) + [value])
    
    # Ensure all rows have the same number of columns
    for row in data:
        while len(row) < (2 + max_indices):
            row.insert(1, "")  # Insert empty string for missing index values
    
    # Create column headers dynamically
    index_columns = [f"Index{i+1}" for i in range(max_indices)]
    columns = ["Variable"] + index_columns + ["Value"]
    
    # Create DataFrame and export to CSV
    df = pd.DataFrame(data, columns=columns)
    df.to_csv(filename, index=False)
    
    print(f"Optimal solution exported to {filename}")

# Example usage (assuming the model is solved)
# export_optimal_values(model)
