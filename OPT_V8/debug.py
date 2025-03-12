import pandapower as pp
import pandas as pd
from pyomo.core import Var
import math
import plotly.graph_objects as go
from utils import *


def test(BUS, LINES):
    number_slack = 0
    number_sub = 0
    number_lv_load = 0
    number_mv_load = 0

    for bus in BUS:
        if BUS[bus].b_type == 'HV_sub':
            number_slack += 1
        elif BUS[bus].b_type == 'MV_sub':
            number_sub += 1
        elif BUS[bus].b_type == 'LV_load':
            print(BUS[bus].load_kW)
            number_lv_load += 1
        elif BUS[bus].b_type == 'MV_load':
            number_mv_load += 1

    print("\nSystem Summary:")
    print("=========================")
    print(f"High Voltage Substations : {number_slack}")
    print(f"Medium Voltage Substations: {number_sub}")
    print(f"Low Voltage Loads        : {number_lv_load}")
    print(f"Medium Voltage Loads     : {number_mv_load}")
    print("=========================\n")

def test_plot(LBUS, SUBS, SLACK, LINES):
    x_max = 0
    y_max = 0
    x_min = 99
    y_min = 99

    # Get the max and min coordinates from both LBUS and SUBS
    for BUS in LBUS:
        x_max = max(x_max, LBUS[BUS].x_coord)
        y_max = max(y_max, LBUS[BUS].y_coord)
        x_min = min(x_min, LBUS[BUS].x_coord)
        y_min = min(y_min, LBUS[BUS].y_coord)

    for BUS in SUBS:
        x_max = max(x_max, SUBS[BUS].x_coord)
        y_max = max(y_max, SUBS[BUS].y_coord)
        x_min = min(x_min, SUBS[BUS].x_coord)
        y_min = min(y_min, SUBS[BUS].y_coord)

    for BUS in SLACK:
        x_max = max(x_max, SLACK[BUS].x_coord)
        y_max = max(y_max, SLACK[BUS].y_coord)
        x_min = min(x_min, SLACK[BUS].x_coord)
        y_min = min(y_min, SLACK[BUS].y_coord)
    
    
    # Extend the bounds a little
    x_max = x_max + 10
    y_max = y_max + 10
    x_min = x_min - 10
    y_min = y_min - 10

    import matplotlib.pyplot as plt

    plt.figure(figsize=(10, 10))
    plt.xlim(x_min, x_max)
    plt.ylim(y_min, y_max)

    # Plot LBUS
    type_markers = {
        "HV_sub": ("s", "red"),   # Square, Red
        "MV_sub": ("D", "orange"), # Diamond, Orange
        "LV_sub": ("^", "yellow"), # Triangle, Yellow
        "MV_load": ("o", "green"), # Circle, Green
        "LV_load": ("x", "blue")   # X, Blue
    }

    for bus in LBUS | SUBS | SLACK:
        if bus in LBUS:
            x = LBUS[bus].x_coord
            y = LBUS[bus].y_coord
            b_type = LBUS[bus].b_type  # Assuming each bus has a 'p_type' attribute
        elif bus in SLACK:
            x = SLACK[bus].x_coord
            y = SLACK[bus].y_coord
            b_type = SLACK[bus].b_type  # Assuming each substation has a 'p_type' attribute
        else:
            x = SUBS[bus].x_coord
            y = SUBS[bus].y_coord
            b_type = SUBS[bus].b_type
            
        
        marker, color = type_markers.get(b_type, ("o", "black"))  # Default to black circle if unknown
        plt.scatter(x, y, s=100, c=color, marker=marker, label=b_type)

    # Plot lines based on the activated lines and conductors
    for line in LINES:
        from_bus = LINES[line].from_bus
        to_bus = LINES[line].to_bus

        # Check if the bus is from LBUS or SUBS and retrieve the correct coordinates
        if from_bus in LBUS:
            from_bus_coords = (LBUS[from_bus].x_coord, LBUS[from_bus].y_coord)
        elif from_bus in SUBS:
            from_bus_coords = (SUBS[from_bus].x_coord, SUBS[from_bus].y_coord)
        else:
            from_bus_coords = (SLACK[from_bus].x_coord, SLACK[from_bus].y_coord)

        if to_bus in LBUS:
            to_bus_coords = (LBUS[to_bus].x_coord, LBUS[to_bus].y_coord)
        elif to_bus in SUBS:
            to_bus_coords = (SUBS[to_bus].x_coord, SUBS[to_bus].y_coord)
        else:
            to_bus_coords = (SLACK[to_bus].x_coord, SLACK[to_bus].y_coord)

        # Plot the line with dashed style if not activated
        plt.plot([from_bus_coords[0], to_bus_coords[0]],
                    [from_bus_coords[1], to_bus_coords[1]],
                    linestyle=':', color='black')
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.title('Bus Locations')
    plt.grid(True)
    plt.show()

def export_optimal_values(model, setting):
    filename = f"optimal_values_{setting[0]}_{setting[1]}_{setting[2]}_{setting[3]}.csv"
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


def debug_pandapower_net(net, filename="network_debug.txt"):
    """
    Saves all Pandapower network elements to a text file for debugging.

    Parameters:
    - net: pandapower network
    - filename: name of the text file (default: network_debug.txt)
    """
    with open(filename, "w") as f:
        f.write("Pandapower Network Debug Info\n")
        f.write("=" * 50 + "\n")

        # Print all network elements
        for element in net.keys():
            if isinstance(net[element], pp.pd.DataFrame) and not net[element].empty:
                f.write(f"\n{element.upper()}:\n")
                f.write(net[element].to_string() + "\n")
                f.write("-" * 50 + "\n")

    print(f"Debug info saved to {filename}")

# Example usage:
# net = pp.networks.case_ieee30()  # Load an example network
# debug_pandapower_net(net)

def plot_comparisons(net, results, model, pp_bus_map, setting):
    """
    Plots voltage magnitude, line current, and power loss comparisons between 
    the optimization model and power flow results.
    
    Parameters:
        net        : The pandapower network model.
        results    : Dictionary containing power flow results for each timestep.
        model      : The optimization model containing voltage values.
        pp_bus_map : Mapping from model bus IDs to pandapower bus indices.
    """
    
    for t, res in results.items():
        if res == "Power flow did not converge":
            continue

        debug_pandapower_net(res, f"powerflow_results_t{t}.txt")

        # Prepare voltage data
        opt_voltages, pf_voltages, bus_labels = [], [], []
        for bus_id in model.B:
            if bus_id not in pp_bus_map:
                continue
            pp_bus = pp_bus_map[bus_id]
            try:
                pf_voltage = res["bus"].loc[pp_bus, 'vm_pu']
            except KeyError:
                continue
            opt_voltages.append(math.sqrt(model.voltage_squared[t, bus_id].value))
            pf_voltages.append(pf_voltage)
            bus_labels.append(str(bus_id))
        
        # Prepare current & loss data
        opt_currents, pf_currents = [], []
        opt_losses, pf_losses = [], []
        line_labels = []
        
        for line_id in model.lines:
            pp_line = net.line[net.line.name == f"Line {line_id}"].index
            if pp_line.empty:
                continue
            pp_line = pp_line[0]
            
            # Get per-unit current
            pf_current = res["line"].loc[pp_line, 'i_ka'] * 1000 * math.sqrt(3) # Convert kA to A
            base_current = BASE_I_MV if net.bus.loc[net.line.loc[pp_line, 'from_bus'], 'vn_kv'] == 15 else BASE_I_LV
            pf_currents.append(pf_current / base_current)
            opt_currents.append(math.sqrt(model.current_squared[t, line_id].value))
            
            # Get per-unit power loss
            pf_loss = res["line"].loc[pp_line, 'pl_mw'] * 1e6 / BASE_POWER
            opt_loss = model.losses[t, line_id].value
            pf_losses.append(pf_loss)
            opt_losses.append(opt_loss)
            line_labels.append(str(line_id))

        # Create vectors for opt and pf values
        opt_values = (opt_voltages, opt_currents, opt_losses)
        pf_values = (pf_voltages, pf_currents, pf_losses)

        esperiment = (opt_values, pf_values)

        max_volt = max(max(opt_voltages), max(pf_voltages))
        max_curr = max(max(opt_currents), max(pf_currents))
        max_loss = max(max(opt_losses), max(pf_losses))

        min_volt = min(min(opt_voltages), min(pf_voltages))
        min_curr = min(min(opt_currents), min(pf_currents))
        min_loss = min(min(opt_losses), min(pf_losses))
        
        # Create figure and subplots
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        # Voltage Comparison
        ax = axes[0]
        ax.scatter(opt_voltages, pf_voltages, color='blue', label='Normalized Bus Voltages')
        for i, label in enumerate(bus_labels):
            ax.text(opt_voltages[i], pf_voltages[i], label, fontsize=9, ha='right', color='blue')
        ax.plot([min_volt, max_volt], [min_volt, max_volt], linestyle='dashed', color='black', label='Unity Line')
        ax.set_title(f"Voltage Comparison at Timestep {t}")
        ax.set_xlabel("Optimization (Normalized)")
        ax.set_ylabel("Power Flow (Normalized)")
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.6)
        
        # Current Comparison
        ax = axes[1]
        ax.scatter(opt_currents, pf_currents, color='red', label='Normalized Line Currents')
        for i, label in enumerate(line_labels):
            ax.text(opt_currents[i], pf_currents[i], label, fontsize=9, ha='right', color='red')
        ax.plot([min_curr, max_curr], [min_curr, max_curr], linestyle='dashed', color='black', label='Unity Line')
        ax.set_title(f"Current Comparison at Timestep {t}")
        ax.set_xlabel("Optimization (Normalized)")
        ax.set_ylabel("Power Flow (Normalized)")
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.6)
        
        # Power Loss Comparison
        ax = axes[2]
        ax.scatter(opt_losses, pf_losses, color='green', label='Normalized Power Losses')
        ax.plot([min_loss, max_loss], [min_loss, max_loss], linestyle='dashed', color='black', label='Unity Line')
        ax.set_title(f"Power Loss Comparison at Timestep {t}")
        ax.set_xlabel("Optimization (Normalized)")
        ax.set_ylabel("Power Flow (Normalized)")
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.6)
        
        # Adjust layout and save the figure
        plt.tight_layout()
        name = f"comparison_{setting[0]}_{setting[1]}_{setting[2]}_{setting[3]}_t{t}.png"
        plt.savefig(name, dpi=300, bbox_inches='tight')

    return esperiment

def plot_comparisons_normalized(net, results, model, pp_bus_map, setting):
    """
    Plots voltage magnitude, line current, and power loss comparisons between 
    the optimization model and power flow results.
    
    Parameters:
        net        : The pandapower network model.
        results    : Dictionary containing power flow results for each timestep.
        model      : The optimization model containing voltage values.
        pp_bus_map : Mapping from model bus IDs to pandapower bus indices.
    """


    def normalize(value, min_val, max_val):
        return (value - min_val) / (max_val - min_val) if max_val > min_val else 0.5  # Avoid division by zero
    
    for t, res in results.items():
        if res == "Power flow did not converge":
            continue

        debug_pandapower_net(res, f"powerflow_results_t{t}.txt")

        # Prepare voltage data
        opt_voltages, pf_voltages, bus_labels = [], [], []
        for bus_id in model.B:
            if bus_id not in pp_bus_map:
                continue
            pp_bus = pp_bus_map[bus_id]
            try:
                pf_voltage = res["bus"].loc[pp_bus, 'vm_pu']
            except KeyError:
                continue
            opt_voltages.append(math.sqrt(model.voltage_squared[t, bus_id].value))
            pf_voltages.append(pf_voltage)
            bus_labels.append(str(bus_id))
        
        # Prepare current & loss data
        opt_currents, pf_currents = [], []
        opt_losses, pf_losses = [], []
        line_labels = []
        
        for line_id in model.lines:
            pp_line = net.line[net.line.name == f"Line {line_id}"].index
            if pp_line.empty:
                continue
            pp_line = pp_line[0]
            
            # Get per-unit current
            pf_current = res["line"].loc[pp_line, 'i_ka'] * 1000 * math.sqrt(3) # Convert kA to A
            base_current = BASE_I_MV if net.bus.loc[net.line.loc[pp_line, 'from_bus'], 'vn_kv'] == 15 else BASE_I_LV
            pf_currents.append(pf_current / base_current)
            opt_currents.append(math.sqrt(model.current_squared[t, line_id].value))
            
            # Get per-unit power loss
            pf_loss = res["line"].loc[pp_line, 'pl_mw'] * 1e6 / BASE_POWER
            opt_loss = model.losses[t, line_id].value
            pf_losses.append(pf_loss)
            opt_losses.append(opt_loss)
            line_labels.append(str(line_id))

        # Compute min-max values for normalization
        min_v, max_v = min(pf_voltages + opt_voltages), max(pf_voltages + opt_voltages)
        min_c, max_c = min(pf_currents + opt_currents), max(pf_currents + opt_currents)
        min_p, max_p = min(pf_losses + opt_losses), max(pf_losses + opt_losses)

        # Normalize values
        norm_opt_voltages = [normalize(v, min_v, max_v) for v in opt_voltages]
        norm_pf_voltages = [normalize(v, min_v, max_v) for v in pf_voltages]
        norm_opt_currents = [normalize(v, min_c, max_c) for v in opt_currents]
        norm_pf_currents = [normalize(v, min_c, max_c) for v in pf_currents]
        norm_opt_losses = [normalize(v, min_p, max_p) for v in opt_losses]
        norm_pf_losses = [normalize(v, min_p, max_p) for v in pf_losses]

        # Create vectors for opt and pf values
        opt_values = norm_opt_voltages + norm_opt_currents + norm_opt_losses
        pf_values = norm_pf_voltages + norm_pf_currents + norm_pf_losses

        esperiment = (opt_values, pf_values)

        max_dei_norm = max(max(norm_opt_voltages), max(norm_pf_voltages), max(norm_opt_currents), max(norm_pf_currents), max(norm_opt_losses))

        # Create figure and axis
        fig, ax = plt.subplots(figsize=(8, 6))

        # Plot Voltage Comparison
        ax.scatter(norm_opt_voltages, norm_pf_voltages, color='blue', label='Normalized Bus Voltages')
        for i, label in enumerate(bus_labels):
            ax.text(norm_opt_voltages[i], norm_pf_voltages[i], label, fontsize=9, ha='right', color='blue')

        # Plot Current Comparison
        ax.scatter(norm_opt_currents, norm_pf_currents, color='red', label='Normalized Line Currents')
        for i, label in enumerate(line_labels):
            ax.text(norm_opt_currents[i], norm_pf_currents[i], label, fontsize=9, ha='right', color='red')

        # Plot Power Loss Comparison
        ax.scatter(norm_opt_losses, norm_pf_losses, color='green', label='Normalized Power Losses')

        # Unity Line (y = x)
        ax.plot([0, max_dei_norm], [0, max_dei_norm], linestyle='dashed', color='black', label='Unity Line')

        # Labels and Title
        ax.set_title(f"Comparison at Timestep {t}")
        ax.set_xlabel("Optimization (Normalized)")
        ax.set_ylabel("Power Flow (Normalized)")
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.6)

        # Save the figure
        name = f"comparison_{setting[0]}_{setting[1]}_{setting[2]}_{setting[3]}_t{t}.png"
        plt.savefig(name, dpi=300, bbox_inches='tight')  # High-quality save


    return esperiment

import pandapower as pp
import pandapower.networks as pn
from pandapower.plotting.plotly import simple_plotly, pf_res_plotly
import numpy as np
from sklearn.linear_model import LinearRegression
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

def table_result(settings, folder_name):
    # Initialize a list to store the table data
    table_data = []

    # Create figure for the plot
    plt.figure(figsize=(8, 6))  # Set figure size

    for i, (setting, data) in enumerate(settings.items()):
        (opt_values, pf_values), logg = data  # Extract logg from the experiment

        # Ensure data is in 2D shape for sklearn
        opt_values = np.array(opt_values).reshape(-1, 1)
        pf_values = np.array(pf_values).reshape(-1, 1)

        # Fit the linear regression model
        model = LinearRegression()
        model.fit(opt_values, pf_values)

        # Get the slope and intercept
        slope = model.coef_[0][0]
        intercept = model.intercept_[0]

        # Generate points for the fitted line
        x_fit = np.linspace(0, 1, 100).reshape(-1, 1)
        y_fit = model.predict(x_fit)

        # Plot scatter points
        plt.scatter(opt_values, pf_values, alpha=0.6)

        # Plot the fitted regression line
        plt.plot(x_fit, y_fit, label=f'Fit {setting[0]}_{setting[1]}_{setting[2]}_{setting[3]} (slope={slope:.2f})', linestyle='--')

        execution_time = logg["execution_time"]
        gap = logg["gap"]

        # Add setting values, execution time, and gap to the table data
        row = list(setting) + [execution_time, gap]
        table_data.append(row)

    # Plot unity line (y = x)
    plt.plot([0, 1], [0, 1], linestyle='dashed', color='black', label='Unity Line')

    # Labels and title
    plt.xlabel("Optimization (Normalized)")
    plt.ylabel("Power Flow (Normalized)")
    plt.title("Comparison with Linear Fit")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)

    # Save the plot
    plt.savefig(f"Scatter_{folder_name}.png", dpi=300, bbox_inches='tight')  # High-quality save

    # Create a pandas DataFrame for the table
    column_names = ['Power setting','NPWB','Capacity setting','NLC']  # Dynamically create setting columns
    column_names += ['Execution Time', 'Gap']

    df = pd.DataFrame(table_data, columns=column_names)

    # Print the table
    print(df)

    # Optionally, you can save the table to a CSV or Excel file
    df.to_csv(f"{folder_name}.csv", index=False)  # Save as CSV

def table_result_2(settings, folder_name):
    # Initialize a list to store the table data
    table_data = []

    for setting, (pf_vs_opt, logg) in settings.items():
        # Detect if pf_vs_opt is a list of tuples (for multiple comparisons)
        is_list_of_tuples = isinstance(pf_vs_opt, list) and all(isinstance(i, tuple) for i in pf_vs_opt)

        if is_list_of_tuples:
            fig, axes = plt.subplots(1, 3, figsize=(18, 6))  # Create subplots for separate comparisons
            comparisons = ["Voltage", "Current", "Power Loss"]
            colors = ["blue", "red", "green"]

            for idx, ((opt_values, pf_values), title, color) in enumerate(zip(pf_vs_opt, comparisons, colors)):
                ax = axes[idx]
                opt_values = np.array(opt_values).reshape(-1, 1)
                pf_values = np.array(pf_values).reshape(-1, 1)

                # Fit linear regression model
                model = LinearRegression()
                model.fit(opt_values, pf_values)
                slope = model.coef_[0][0]

                # Generate fit line
                x_fit = np.linspace(opt_values.min(), opt_values.max(), 100).reshape(-1, 1)
                y_fit = model.predict(x_fit)

                # Scatter plot and regression line
                ax.scatter(opt_values, pf_values, alpha=0.6, color=color)
                ax.plot(x_fit, y_fit, linestyle="--", label=f"Fit {setting} (slope={slope:.2f})", color=color)
                ax.plot([opt_values.min(), opt_values.max()], [opt_values.min(), opt_values.max()], linestyle="dashed", color="black", label="Unity Line")

                # Labels and grid
                ax.set_xlabel("Optimization (Normalized)")
                ax.set_ylabel("Power Flow (Normalized)")
                ax.set_title(f"{title} Comparison at Timestep {setting}")
                ax.legend()
                ax.grid(True, linestyle="--", alpha=0.6)

        else:  # Single tuple case
            plt.figure(figsize=(8, 6))
            opt_values, pf_values = pf_vs_opt
            opt_values = np.array(opt_values).reshape(-1, 1)
            pf_values = np.array(pf_values).reshape(-1, 1)

            # Fit linear regression model
            model = LinearRegression()
            model.fit(opt_values, pf_values)
            slope = model.coef_[0][0]

            # Generate fit line
            x_fit = np.linspace(opt_values.min(), opt_values.max(), 100).reshape(-1, 1)
            y_fit = model.predict(x_fit)

            # Scatter plot and regression line
            plt.scatter(opt_values, pf_values, alpha=0.6)
            plt.plot(x_fit, y_fit, linestyle="--", label=f"Fit {setting} (slope={slope:.2f})")
            plt.plot([opt_values.min(), opt_values.max()], [opt_values.min(), opt_values.max()], linestyle="dashed", color="black", label="Unity Line")

            plt.xlabel("Optimization (Normalized)")
            plt.ylabel("Power Flow (Normalized)")
            plt.title(f"Comparison at Timestep {setting}")
            plt.legend()
            plt.grid(True, linestyle="--", alpha=0.6)

        # Save Figure
        plt.tight_layout()
        plt.savefig(f"Scatter_{folder_name}.png", dpi=300, bbox_inches='tight')  # High-quality save

        
        # Extract execution data
        execution_time = logg["execution_time"]
        gap = logg["gap"]

        # Append to table data
        table_data.append([setting, execution_time, gap])

    # Save Table as CSV
    df = pd.DataFrame(table_data, columns=["Setting", "Execution Time", "Gap"])
    df.to_csv(f"{folder_name}.csv", index=False)  # Save as CSV
    return df

def precision(esperiment):
    x,y = esperiment
    return (sum(i for i in x) - sum(i for i in y)) / sum(i for i in y) * 100

def easy_plot(net, setting):
    file_name = f"easy_plot_{setting[0]}_{setting[1]}_{setting[2]}_{setting[3]}.html"
    # Run power flow before plotting results
    pp.runpp(net)
    
    # Generate simple plot
    fig_simple = simple_plotly(net)
    fig_simple.write_html(file_name+'_simple')
    
    # Generate power flow results plot
    fig_pf = pf_res_plotly(net)
    fig_pf.write_html(file_name+'_pf')

