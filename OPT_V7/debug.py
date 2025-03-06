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

def plot_comparisons(net, results, model, pp_bus_map):
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
            opt_voltages.append(math.sqrt(model.voltage_squared[t+1, bus_id].value))
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
            opt_currents.append(math.sqrt(model.current_squared[t+1, line_id].value))
            
            # Get per-unit power loss
            pf_loss = res["line"].loc[pp_line, 'pl_mw'] * 10**6 / BASE_POWER
            opt_loss = model.losses[t+1, line_id].value
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

        # Create plots
        fig = go.Figure()
        
        # Voltage comparison
        fig.add_trace(go.Scatter(
            x=norm_opt_voltages, y=norm_pf_voltages, mode='markers+text',
            text=bus_labels, textposition="top center",
            marker=dict(size=10, color='blue'),
            name='Normalized Bus Voltages'
        ))
        
        # Current comparison
        fig.add_trace(go.Scatter(
            x=norm_opt_currents, y=norm_pf_currents, mode='markers+text',
            text=line_labels, textposition="top center",
            marker=dict(size=10, color='red'),
            name='Normalized Line Currents'
        ))
        
        # Power loss comparison
        fig.add_trace(go.Scatter(
            x=norm_opt_losses, y=norm_pf_losses, mode='markers+text',
            text=line_labels, textposition="top center",
            marker=dict(size=10, color='green'),
            name='Normalized Power Losses'
        ))

        # Add Unity Line (y = x)
        fig.add_trace(go.Scatter(
            x=[0, 1], y=[0, 1], mode='lines',
            line=dict(color='black', dash='dash'),
            name='Unity Line'
        ))

        fig.update_layout(
            title=f"Comparison at Timestep {t+1}",
            xaxis_title="Optimization (Normalized)",
            yaxis_title="Power Flow (Normalized)",
            template="plotly_white"
        )

        fig.show()

    return

