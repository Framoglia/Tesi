import pandapower as pp
import pandas as pd
from pyomo.environ import Var, Param, Expression
import math
import csv
import plotly.graph_objects as go
from utils import *
import plotly.io as pio
pio.renderers.default = "notebook"
import os
import shutil
import glob
from datetime import datetime
import matplotlib.pyplot as plt
from pandapower.plotting.plotly import simple_plotly, pf_res_plotly
from pyomo.environ import value  # Import Pyomo's value() function
import seaborn as sns

def plot_opt(m, LBUS, SUBS, SLACK, LINES, LINES_OPT, N_PERIODS):
    # Combine all buses from different categories into one list
    all_buses = LBUS | SUBS| SLACK

    # Get all x and y coordinates
    x_coords = [bus.x_coord for bus in all_buses.values()]
    y_coords = [bus.y_coord for bus in all_buses.values()]

    # Calculate max and min coordinates
    x_max = max(x_coords) + 10
    y_max = max(y_coords) + 10
    x_min = min(x_coords) - 10
    y_min = min(y_coords) - 10

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

    for bus in m.B | m.subs_hv:
        if bus in m.buses:
            x = LBUS[bus].x_coord
            y = LBUS[bus].y_coord
            b_type = LBUS[bus].b_type  # Assuming each bus has a 'p_type' attribute
        elif bus in m.subs_hv:
            x = SLACK[bus].x_coord
            y = SLACK[bus].y_coord
            b_type = SLACK[bus].b_type  # Assuming each substation has a 'p_type' attribute
        else:
            x = SUBS[bus].x_coord
            y = SUBS[bus].y_coord
            b_type = SUBS[bus].b_type
            
        
        marker, color = type_markers.get(b_type, ("o", "black"))  # Default to black circle if unknown
        plt.scatter(x, y, s=100, c=color, marker=marker, label=b_type if bus == list(m.B)[0] else "")

    # Assuming 'LINES_OPT' is already defined, and it contains the necessary information for each conductor
    # Sort the conductors by 'imax' values
    conductors = sorted(LINES_OPT, key=lambda conductor: LINES_OPT[conductor].imax_kA)

    

    # Create a monochromatic colormap based on the number of unique conductors
    num_conductors = len(conductors)
    colormap = cm.get_cmap('Blues', num_conductors)  # 'Blues' colormap
    colormap = colormap(np.linspace(0.3, 1, num_conductors))  # Start at 0.3 to avoid the very light colors

    # Create a mapping from code_word to color
    color_mapping = {code_word: colormap[i] for i, code_word in enumerate(conductors)}

    # Add a legend for the code words and their corresponding colors
    for code_word, color in color_mapping.items():
        plt.plot([], [], color=color, label=code_word)

    plt.legend()


    # Plot lines based on the activated lines and conductors
    for line in m.lines:
        ##DEBUG   print(f"Checking line {line}")
        if m.line_act[line].value >= 0.8 :  # If line is activated
            ##DEBUG   print(f"Line {line} is activated.")
            
            # Get from_bus and to_bus based on whether they are LBUS or SUBS
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

            # Plot the line with the conductor selected
            for conductor in m.conductors:
                ##DEBUG    print(f"Conductor {conductor} activation status: {m.line_opt[line,conductor].value}")
                if m.line_opt[line, conductor].value >= 0.8:  # If this conductor is selected
                    ##DEBUG     print(f"  Conductor {conductor} is used for this line.")
                    # Get the color corresponding to the line's conductor
                    color = color_mapping.get(conductor, 'black')  # defaults to 'black' if line_id not found
                    plt.plot([from_bus_coords[0], to_bus_coords[0]],
                            [from_bus_coords[1], to_bus_coords[1]],
                            linestyle='-', color=color, linewidth=3)
                    
            
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.title('Bus Locations')
    plt.legend()
    plt.grid(True)
    name=f"optimal_topology.png"
    plt.savefig(name)
    plt.close()

################################################################################################################

def plot_opt_district(district_results, SLACK, LINES_OPT):

    LBUS = {}
    SUBS = {}
    LINES = {}
    cond_table = {}

    for district in district_results.keys():
        LBUS.update(district_results[district]["LBUS"])
        SUBS.update(district_results[district]["SUBS"])
        LINES.update(district_results[district]["LINES"])
        cond_table.update(district_results[district]["cond_table"])

    all_buses = LBUS | SUBS| SLACK

    # Get all x and y coordinates
    x_coords = [bus.x_coord for bus in all_buses.values()]
    y_coords = [bus.y_coord for bus in all_buses.values()]

    # Calculate max and min coordinates
    x_max = max(x_coords) + 10
    y_max = max(y_coords) + 10
    x_min = min(x_coords) - 10
    y_min = min(y_coords) - 10

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

    for bus in all_buses.keys():
        x = all_buses[bus].x_coord
        y = all_buses[bus].y_coord
        b_type = all_buses[bus].b_type
            
        marker, color = type_markers.get(b_type, ("o", "black"))  # Default to black circle if unknown
        plt.scatter(x, y, s=100, c=color, marker=marker, label=b_type)

    conductors = sorted(LINES_OPT, key=lambda conductor: LINES_OPT[conductor].imax_kA)

    # Create a monochromatic colormap based on the number of unique conductors
    num_conductors = len(conductors)
    colormap = cm.get_cmap('Blues', num_conductors)  # 'Blues' colormap
    colormap = colormap(np.linspace(0.3, 1, num_conductors))  # Start at 0.3 to avoid the very light colors

    # Create a mapping from code_word to color
    color_mapping = {code_word: colormap[i] for i, code_word in enumerate(conductors)}

    # Add a legend for the code words and their corresponding colors
    for code_word, color in color_mapping.items():
        plt.plot([], [], color=color, label=code_word)

    plt.legend()


    # Plot lines based on the activated lines and conductors
    for line in LINES.keys():

        from_bus = LINES[line].from_bus
        to_bus = LINES[line].to_bus

        from_bus_coords = (all_buses[from_bus].x_coord, all_buses[from_bus].y_coord)
        to_bus_coords = (all_buses[to_bus].x_coord, all_buses[to_bus].y_coord)

        conductor = None

        for cond_id in LINES_OPT.keys():
            if cond_table[line][cond_id] == 1:
                conductor = cond_id
                break

        color = color_mapping.get(conductor, 'black')  # defaults to 'black' if line_id not found
        plt.plot([from_bus_coords[0], to_bus_coords[0]],
                [from_bus_coords[1], to_bus_coords[1]],
                linestyle='-', color=color, linewidth=3)
                    
            
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.title('Bus Locations')
    plt.legend()
    plt.grid(True)
    name=f"optimal_topology.png"
    plt.savefig(name)
    plt.close()

################################################################################################################

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

################################################################################################################
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm

def plot_topology_basic(LBUS, SUBS, SLACK, LINES):

    # Determine plot bounds
    BUS_SET = LBUS | SUBS | SLACK     

    x_coords = [data.x_coord for data in BUS_SET.values()]
    y_coords = [data.y_coord for data in BUS_SET.values()]

    x_max = max(x_coords) +10
    x_min = min(x_coords) -10
    y_max = max(y_coords) +10
    y_min = min(y_coords) -10

    plt.figure(figsize=(10, 10))
    plt.xlim(x_min, x_max)
    plt.ylim(y_min, y_max)

    # Define markers/colors by type
    type_markers = {
        "HV_sub": ("s", "red"),
        "MV_sub": ("D", "orange"),
        "LV_sub": ("^", "yellow"),
        "MV_load": ("o", "green"),
        "LV_load": ("x", "blue")
    }

    # Plot LBUS
    for bus in LBUS:
        x = LBUS[bus].x_coord
        y = LBUS[bus].y_coord
        b_type = LBUS[bus].b_type
        marker, color = type_markers.get(b_type, ("o", "black"))
        plt.scatter(x, y, s=100, c=color, marker=marker, label=b_type)

    # Plot SUBS
    for bus in SUBS:
        x = SUBS[bus].x_coord
        y = SUBS[bus].y_coord
        b_type = SUBS[bus].b_type
        marker, color = type_markers.get(b_type, ("o", "black"))
        plt.scatter(x, y, s=100, c=color, marker=marker, label=b_type)

    # Plot SLACK
    for bus in SLACK:
        x = SLACK[bus].x_coord
        y = SLACK[bus].y_coord
        b_type = SLACK[bus].b_type
        marker, color = type_markers.get(b_type, ("o", "black"))
        plt.scatter(x, y, s=100, c=color, marker=marker, label=b_type)

    # Plot lines - all with the same color and linewidth
    for line in LINES:
        from_bus = LINES[line].from_bus
        to_bus = LINES[line].to_bus

        # Get coordinates
        def get_coords(bus):
            if bus in LBUS:
                return LBUS[bus].x_coord, LBUS[bus].y_coord
            elif bus in SUBS:
                return SUBS[bus].x_coord, SUBS[bus].y_coord
            elif bus in SLACK:
                return SLACK[bus].x_coord, SLACK[bus].y_coord
            else:
                return (0, 0)  # Default in case it's missing

        x1, y1 = get_coords(from_bus)
        x2, y2 = get_coords(to_bus)

        plt.plot([x1, x2], [y1, y2], linestyle='-', color='black', linewidth=2)

    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.title('Network Topology (Simple)')
    plt.grid(True)
    plt.savefig("topology_basic.png")
    plt.close()


################################################################################################################

def export_optimal_values(model, count=0,  blacklist=[]): 
    """
    Export optimal solution values for variables, parameters, and expressions not in the blacklist.
    Saves as 'optimal_values.csv'.
    """
    filename = f"optimal_values_{count}.csv"
    rows = []
    global_sets = []
    comp_set_map = {}

    # Collect Var, Param, and Expression components
    components = (
        list(model.component_objects(Var, active=True)) +
        list(model.component_objects(Param, active=True)) +
        list(model.component_objects(Expression, active=True))
    )
    
    # FIRST PASS: Determine the sets over which each component is defined
    for comp in components:
        comp_name = comp.local_name
        if comp_name in blacklist:
            continue
        
        if comp.is_indexed():
            try:
                idx_tuple = comp.index_set().subsets(expand_all_set_operators=False)
            except AttributeError:
                idx_tuple = (comp.index_set(),)
            idx_names = []
            for s in idx_tuple:
                try:
                    set_name = s.local_name
                except AttributeError:
                    set_name = str(s)
                idx_names.append(set_name)
                if set_name not in global_sets:
                    global_sets.append(set_name)
        else:
            idx_names = []
            
        comp_set_map[comp_name] = idx_names
    
    # Helper function to process any component type
    def process_component(comp_type):
        for comp in model.component_objects(comp_type, active=True):
            comp_name = comp.local_name
            if comp_name in blacklist:
                continue

            idx_names = comp_set_map.get(comp_name, [])
            if comp.is_indexed():
                for index in comp:
                    try:
                        val = value(comp[index])
                    except:
                        val = float('nan')
                    index_tuple = index if isinstance(index, tuple) else (index,)
                    row = [comp_name]
                    for set_name in global_sets:
                        if set_name in idx_names:
                            pos = idx_names.index(set_name)
                            row.append(index_tuple[pos] if pos < len(index_tuple) else float('nan'))
                        else:
                            row.append(float('nan'))
                    row.append(val)
                    rows.append(row)
            else:
                try:
                    val = value(comp)
                except:
                    val = float('nan')
                row = [comp_name] + [float('nan')] * len(global_sets) + [val]
                rows.append(row)


    # Process each component type
    process_component(Var)
    process_component(Param)
    process_component(Expression)

    # Final output
    header = ["Name"] + global_sets + ["Value"]
    df = pd.DataFrame(rows, columns=header)
    df.to_csv(filename, index=False)

################################################################################################################

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

################################################################################################################

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
    
    for t, res in results.items():
        if res == "Power flow did not converge":
            continue

        #debug_pandapower_net(res, f"powerflow_results_t{t}.txt")

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
            pf_current = res["line"].loc[pp_line, 'i_ka'] * math.sqrt(3) # Convert kA to A
            base_current = BASE_I_MV if net.bus.loc[net.line.loc[pp_line, 'from_bus'], 'vn_kv'] == 15 else BASE_I_LV
            pf_currents.append(pf_current)
            opt_currents.append(math.sqrt(model.current_squared[t, line_id].value)*base_current/1000)
            
            # Get per-unit power loss
            pf_loss = res["line"].loc[pp_line, 'pl_mw'] 
            opt_loss = model.losses[t, line_id].value * BASE_POWER / 1e6
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
        ax.scatter(opt_voltages, pf_voltages, color='blue', label='Bus Voltages [p.u.]')
        for i, label in enumerate(bus_labels):
            ax.text(opt_voltages[i], pf_voltages[i], label, fontsize=9, ha='right', color='blue')
        ax.plot([min_volt, max_volt], [min_volt, max_volt], linestyle='dashed', color='black', label='Unity Line')
        ax.set_title(f"Voltage Comparison at Timestep {t}")
        ax.set_xlabel("Optimization")
        ax.set_ylabel("Power Flow")
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.6)
        
        # Current Comparison
        ax = axes[1]
        ax.scatter(opt_currents, pf_currents, color='red', label='Line Currents [kA]')
        for i, label in enumerate(line_labels):
            ax.text(opt_currents[i], pf_currents[i], label, fontsize=9, ha='right', color='red')
        ax.plot([min_curr, max_curr], [min_curr, max_curr], linestyle='dashed', color='black', label='Unity Line')
        ax.set_title(f"Current Comparison at Timestep {t}")
        ax.set_xlabel("Optimization")
        ax.set_ylabel("Power Flow")
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.6)
        
        # Power Loss Comparison
        ax = axes[2]
        ax.scatter(opt_losses, pf_losses, color='green', label='Power Losses [MW]')
        ax.plot([min_loss, max_loss], [min_loss, max_loss], linestyle='dashed', color='black', label='Unity Line')
        ax.set_title(f"Power Loss Comparison at Timestep {t}")
        ax.set_xlabel("Optimization")
        ax.set_ylabel("Power Flow")
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.6)
        
        # Adjust layout and save the figure
        plt.tight_layout()
        name = f"comparison_t{t}.png"
        plt.savefig(name, dpi=300, bbox_inches='tight')
        plt.close()

    return esperiment

################################################################################################################

def plot_comparisons_normalized(net, results, model, pp_bus_map, filename):
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
        name = f"comparison_t{t}_{filename}.png"
        plt.savefig(name, dpi=300, bbox_inches='tight')  # High-quality save
        plt.close()


    return esperiment

################################################################################################################

def pf_hm(results, pp_bus_map, pp_line_map, count=0):
    inv_bus_map = {v: k for k, v in pp_bus_map.items()}
    inv_line_map = {v: k for k, v in pp_line_map.items()}

    voltage_data = {}
    loading_data = {}

    for t, res in results.items():
        # Bus voltages
        if res["bus"] is not None:
            bus_series = res["bus"]["vm_pu"].copy()
            bus_series.index = bus_series.index.map(inv_bus_map)
            voltage_data[t] = bus_series

        # Line loadings
        if res["line"] is not None:
            line_series = res["line"]["loading_percent"].copy()
            line_series.index = line_series.index.map(inv_line_map)
            loading_data[t] = line_series

    # Concatenate and transpose
    voltage_df = pd.concat(voltage_data, axis=1).T
    loading_df = pd.concat(loading_data, axis=1).T

    plt.figure(figsize=(12, 6))
    sns.heatmap(voltage_df, cmap="viridis", cbar_kws={'label': 'Voltage (p.u.)'})
    plt.title("Bus Voltages Over Time")
    plt.xlabel("Original Bus ID")
    plt.ylabel("Time Step")
    plt.tight_layout()
    plt.savefig(f"bus_voltages_{count}.png")
    plt.close()

    # Line Loading Heatmap
    plt.figure(figsize=(12, 6))
    sns.heatmap(loading_df, cmap="magma", cbar_kws={'label': 'Line Loading (%)'})
    plt.title("Line Loadings Over Time")
    plt.xlabel("Original Line ID")
    plt.ylabel("Time Step")
    plt.tight_layout()
    plt.savefig(f"line_loadings_{count}.png")
    plt.close()

    return voltage_df , loading_df

################################################################################################################

def easy_plot(net):
    file_name = f"easy_plot.html"
    # Run power flow before plotting results
    pp.runpp(net)
    
    # Generate simple plot
    fig_simple = simple_plotly(net)
    fig_simple.write_html(file_name+'_simple')
    
    # Generate power flow results plot
    fig_pf = pf_res_plotly(net)
    fig_pf.write_html(file_name+'_pf')

################################################################################################################

import os
os.environ['ORTOOLS_LOGGING'] = 'none'
import glob
import shutil
from datetime import datetime

def move_files_to_folder(folder_name='organized_files'):
    """timestamp = datetime.now().strftime("%d_%m_%H_%M")
    main_folder = f"{folder_name}_{timestamp}" """
    main_folder = f"{folder_name}"
    comparison_folder = os.path.join(main_folder, "comparisons")

    os.makedirs(main_folder, exist_ok=True)
    os.makedirs(comparison_folder, exist_ok=True)

    # File type patterns
    file_types = ['*.pdf', '*.csv', '*.txt', '*.log', '*.lp', '*.pkl', '*.html']

    # Move comparison PNGs to comparison folder
    for file in glob.glob('comparison_t*.png'):
        shutil.move(file, os.path.join(comparison_folder, file))

    # Move other PNGs to main folder
    for file in glob.glob('*.png'):
        if not file.startswith('comparison_t'):
            shutil.move(file, os.path.join(main_folder, file))

    # Move other file types
    for pattern in file_types:
        for file in glob.glob(pattern):
            shutil.move(file, os.path.join(main_folder, file))

    print(f"Moved files to '{main_folder}'.")
    return main_folder  # Return path for grouping

################################################################################################################

def group_folders(folders, group_name='all_organized_folders'):

    if "Bilevel" not in folders:
        timestamp = datetime.now().strftime("%d_%m_%H_%M")
        main_folder = f"{group_name}_{timestamp}" 
    else: 
        main_folder = f"{group_name}"

    os.makedirs(main_folder, exist_ok=True)
    for folder in folders:
        if os.path.exists(folder):
            shutil.move(folder, os.path.join(main_folder, folder))
    shutil.move("optimal_topology.png",os.path.join(main_folder, "optimal_topology.png"))
    print(f"Grouped all folders into '{main_folder}'.")

    return main_folder

################################################################################################################

def plot_network_solution_2(model, LBUS, SUBS, SLACK, LINES, LINES_OPT, count = 0):

    """
    Creates an interactive Plotly figure of the optimized distribution network.
    
    Parameters:
      model      : The solved optimization model.
      LBUS       : Dict of load bus objects with attributes: voltage_level, x_coord, y_coord, and surface.
      SUBS       : Dict of substation objects with attributes: voltage_level, x_coord, y_coord.
      SLACK      : Dict of slack bus objects with attributes: voltage_level, x_coord, y_coord.
      LINES      : Dict of line objects with attributes: from_bus, to_bus, length.
      LINES_OPT  : Dict of conductor objects (keyed by conductor type) with attributes: r_per_km, xl_per_km, imax_kA.
    
    Returns:
      fig        : A Plotly figure with a timestep slider and update buttons.
    """
    import plotly.graph_objects as go

    # ====== CONFIGURATION ======
    bus_type_info = {
        "LV LOAD":  {"color": "blue",   "symbol": "circle",   "name": "LV Load Bus"},
        "MV LOAD":  {"color": "yellow",   "symbol": "circle",   "name": "MV Load Bus"},
        "SUBS":  {"color": "red",    "symbol": "square",   "name": "Substation"},
        "SLACK": {"color": "green",  "symbol": "diamond",  "name": "Slack"}
    }
    not_built_color = "grey"
    
    # Marker symbols and offsets
    pv_symbol      = "star"
    inv_symbol     = "x"
    storage_symbol = "diamond"
    pv_offset      = (2.5, 5)
    inv_offset     = (2.5, 2.5)
    storage_offset = (-2.5, 2.5)
    
    # Conductor colors
    conductor_colors = {
        "Poppy": "#90E0EF",
        "Oxlip": "#00B4D8",
        "Daisy": "#0077B6",
        "Tulip": "#03045E"
    }
    
    # ====== BUILD STATIC TRACES ======
    # -- Load Buses (LBUS) -- static hover info: only the bus id.
    lbus_traces = []
    lbus_by_type = {"LV LOAD": {"x": [], "y": [], "ids": []},
                    "MV LOAD": {"x": [], "y": [], "ids": []}}

    for bus_id, bus in LBUS.items():
        typex = "MV LOAD"
        if bus.voltage_level == 400:
            typex = "LV LOAD"
        lbus_by_type[typex]["x"].append(bus.x_coord)
        lbus_by_type[typex]["y"].append(bus.y_coord)
        lbus_by_type[typex]["ids"].append(bus_id)

    # Create one trace per type
    for typex, data in lbus_by_type.items():
        trace = go.Scatter(
            x=data["x"], y=data["y"],
            mode="markers",
            marker=dict(
                color=bus_type_info[typex]["color"],
                symbol=bus_type_info[typex]["symbol"],
                size=10
            ),
            text=[f"Bus {bus_id}" for bus_id in data["ids"]],
            hoverinfo="text",
            name=bus_type_info[typex]["name"]
        )
        lbus_traces.append(trace)
    
    lv_ids = lbus_by_type["LV LOAD"]["ids"]
    mv_ids = lbus_by_type["MV LOAD"]["ids"]
        
    # -- Substations (SUBS) -- initial texts will be updated dynamically.
    subs_built_x, subs_built_y, subs_built_text = [], [], []
    subs_not_built_x, subs_not_built_y, subs_not_built_text = [], [], []
    for sub_id, sub in SUBS.items():
        if hasattr(model, "gamma") and model.gamma[sub_id].value >= 0.8:
            subs_built_x.append(sub.x_coord)
            subs_built_y.append(sub.y_coord)
            subs_built_text.append(f"Substation {sub_id} (Built)")
        else:
            subs_not_built_x.append(sub.x_coord)
            subs_not_built_y.append(sub.y_coord)
            subs_not_built_text.append(f"Substation {sub_id} (Not Built)")
    
    subs_built_trace = go.Scatter(
        x=subs_built_x, y=subs_built_y,
        mode="markers",
        marker=dict(color=bus_type_info["SUBS"]["color"],
                    symbol=bus_type_info["SUBS"]["symbol"],
                    size=12),
        text=subs_built_text,
        hoverinfo="text",
        name="Substations (Built)"
    )
    subs_not_built_trace = go.Scatter(
        x=subs_not_built_x, y=subs_not_built_y,
        mode="markers",
        marker=dict(color=not_built_color,
                    symbol=bus_type_info["SUBS"]["symbol"],
                    size=12),
        text=subs_not_built_text,
        hoverinfo="text",
        name="Substations (Not Built)"
    )
    
    # -- Slack Buses (SLACK) -- initial texts will be updated dynamically.
    slack_built_x, slack_built_y, slack_built_text = [], [], []
    slack_not_built_x, slack_not_built_y, slack_not_built_text = [], [], []
    for slack_id, slack in SLACK.items():
        if hasattr(model, "beta") and model.beta[slack_id].value >= 0.8:
            slack_built_x.append(slack.x_coord)
            slack_built_y.append(slack.y_coord)
            slack_built_text.append(f"Slack {slack_id} (Active)")
        else:
            slack_not_built_x.append(slack.x_coord)
            slack_not_built_y.append(slack.y_coord)
            slack_not_built_text.append(f"Slack {slack_id} (Not Active)")
    
    slack_built_trace = go.Scatter(
        x=slack_built_x, y=slack_built_y,
        mode="markers",
        marker=dict(color=bus_type_info["SLACK"]["color"],
                    symbol=bus_type_info["SLACK"]["symbol"],
                    size=12),
        text=slack_built_text,
        hoverinfo="text",
        name="Slack (Active)"
    )
    slack_not_built_trace = go.Scatter(
        x=slack_not_built_x, y=slack_not_built_y,
        mode="markers",
        marker=dict(color=not_built_color,
                    symbol=bus_type_info["SLACK"]["symbol"],
                    size=12),
        text=slack_not_built_text,
        hoverinfo="text",
        name="Slack (Not Active)"
    )
    
    # -- Investment markers: PV, Inverters, and Storage Investment.
    pv_x, pv_y, pv_text = [], [], []
    inv_x, inv_y, inv_text = [], [], []
    storage_x, storage_y, storage_text = [], [], []
    for bus_id, bus in LBUS.items():
        # PV installation check
        if model.PV_surf[bus_id].value > 0.5:
            pv_x.append(bus.x_coord + pv_offset[0])
            pv_y.append(bus.y_coord + pv_offset[1])
            pv_text.append(f"PV installed on Bus {bus_id}")
        else:
            pv_x.append('')
            pv_y.append('')
            pv_text.append("")
        # Inverter installation check
        if model.S_inv[bus_id].value > 0.0005:
            inv_x.append(bus.x_coord + inv_offset[0])
            inv_y.append(bus.y_coord + inv_offset[1])
            inv_text.append(f"Inverter installed on Bus {bus_id}")
        else:
            inv_x.append('')
            inv_y.append('')
            inv_text.append("")
        # Storage investment check
        if hasattr(model, "storage_capacity") and model.storage_capacity[bus_id].value > 0.0005:
            storage_x.append(bus.x_coord + storage_offset[0])
            storage_y.append(bus.y_coord + storage_offset[1])
            storage_text.append(f"Storage installed on Bus {bus_id}")
        else:
            storage_x.append('')
            storage_y.append('')
            storage_text.append("")
    
    pv_trace = go.Scatter(
        x=pv_x, y=pv_y,
        mode="markers",
        marker=dict(color="orange", symbol=pv_symbol, size=10),
        text=pv_text,
        hoverinfo="text",
        name="PV Panels"
    )
    inv_trace = go.Scatter(
        x=inv_x, y=inv_y,
        mode="markers",
        marker=dict(color="purple", symbol=inv_symbol, size=10),
        text=inv_text,
        hoverinfo="text",
        name="Inverters"
    )
    storage_trace = go.Scatter(
        x=storage_x, y=storage_y,
        mode="markers",
        marker=dict(color="brown", symbol=storage_symbol, size=10),
        text=storage_text,
        hoverinfo="text",
        name="Storage Investment"
    )
    
    # -- Build Line Traces (Geometry and Midpoint Markers)
    bus_coords = {bus_id: (bus.x_coord, bus.y_coord) for bus_id, bus in LBUS.items()}
    bus_coords.update({sub_id: (sub.x_coord, sub.y_coord) for sub_id, sub in SUBS.items()})
    bus_coords.update({slack_id: (slack.x_coord, slack.y_coord) for slack_id, slack in SLACK.items()})
    
    lines_geom_by_conductor = {}   # For drawing the lines
    midpoints_by_conductor = {}      # For midpoint markers with dynamic hover info
    conductor_order = []  # to maintain order of conductor groups
    t0 = next(iter(model.periods))  # initial timestep
    
    for line_id, line in LINES.items():
        built = False
        if hasattr(model, 'line_act') and model.line_act[line_id].value > 0.8:
            built = True

        if built:
            chosen_conductor = None
            for cond in LINES_OPT.keys():
                if model.line_opt[line_id, cond].value > 0.8:
                    chosen_conductor = cond
                    break
            if chosen_conductor is None:
                chosen_conductor = "unknown"
        else:
            chosen_conductor = "not_built"
        
        if line.from_bus in bus_coords and line.to_bus in bus_coords:
            x0, y0 = bus_coords[line.from_bus]
            x1, y1 = bus_coords[line.to_bus]
            xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
            
            line_hover = ""  # will be updated dynamically in frames
            
            if chosen_conductor not in lines_geom_by_conductor:
                lines_geom_by_conductor[chosen_conductor] = {"x": [], "y": []}
                midpoints_by_conductor[chosen_conductor] = {"x": [], "y": [], "text": []}
                conductor_order.append(chosen_conductor)
            lines_geom_by_conductor[chosen_conductor]["x"].extend([x0, x1, None])
            lines_geom_by_conductor[chosen_conductor]["y"].extend([y0, y1, None])
            midpoints_by_conductor[chosen_conductor]["x"].append(xm)
            midpoints_by_conductor[chosen_conductor]["y"].append(ym)
            midpoints_by_conductor[chosen_conductor]["text"].append(line_hover)
    
    line_traces = []
    midpoint_trace_refs = []  # For dynamic update
    for cond in conductor_order:
        if cond == "not_built":
            color = "grey"
            dash = "dash"
            name = "Not Built"
        else:
            color = conductor_colors.get(cond, "black")
            dash = "solid"
            name = f"Conductor {cond}"
        geom_trace = go.Scatter(
            x=lines_geom_by_conductor[cond]["x"],
            y=lines_geom_by_conductor[cond]["y"],
            mode="lines",
            line=dict(color=color, width=2, dash=dash),
            hoverinfo="none",
            name=name
        )
        midpoint_trace = go.Scatter(
            x=midpoints_by_conductor[cond]["x"],
            y=midpoints_by_conductor[cond]["y"],
            mode="markers",
            marker=dict(color=color, size=8, symbol="circle"),
            text=midpoints_by_conductor[cond]["text"],
            hoverinfo="text",
            name=name + " (Info)"
        )
        line_traces.append(geom_trace)
        line_traces.append(midpoint_trace)
        midpoint_trace_refs.append(midpoint_trace)
    
    # ====== ASSEMBLE THE FIGURE ======
    data = [
        lbus_traces[0],
        lbus_traces[1],
        subs_built_trace,
        subs_not_built_trace,
        slack_built_trace,
        slack_not_built_trace,
        pv_trace,
        inv_trace,
        storage_trace
    ] + line_traces

    fig = go.Figure(data=data)
    
    # ====== BUILD FRAMES FOR TIMESTEP UPDATES ======
    frames = []
    for t in model.periods:
        # Update dynamic hover texts.

        updated_lbus_lv, updated_lbus_mv = [], []
        updated_pv_text_lv, updated_pv_text_mv = [], []
        updated_inv_text_lv, updated_inv_text_mv = [], []
        updated_storage_text_lv, updated_storage_text_mv = [], []

        # --- LV Buses ---
        for bus_id in lv_ids:
            # Load data
            P_val = model.P_bus[t, bus_id].value
            Q_val = model.Q_bus[t, bus_id].value
            updated_lbus_lv.append(
                f"LV Bus {bus_id}<br>Load: {P_val:.3f} MW, {Q_val:.3f} MVAR (Timestep {t})"
            )

            # PV data (if installed)
            if model.PV_surf[bus_id].value > 0.5:
                pv_cap = model.PV_surf[bus_id].value * 1e-3 * 0.2  # Example calculation
                updated_pv_text_lv.append(
                    f"PV on LV Bus {bus_id}<br>Capacity: {pv_cap:.3f} MWp (Timestep {t})"
                )
            else:
                updated_pv_text_lv.append("")

            # Inverter data (if installed)
            if model.S_inv[bus_id].value > 0.0005:
                inv_cap = model.S_inv[bus_id].value
                updated_inv_text_lv.append(
                    f"Inverter on LV Bus {bus_id}<br>Capacity: {inv_cap:.3f} MVAR (Timestep {t})"
                )
            else:
                updated_inv_text_lv.append("")

            # Storage data (if installed)
            if hasattr(model, "storage_capacity") and model.storage_capacity[bus_id].value > 0.0005:
                storage_cap = model.storage_capacity[bus_id].value
                updated_storage_text_lv.append(
                    f"Storage on LV Bus {bus_id}<br>Capacity: {storage_cap:.3f} MWh (Timestep {t})"
                )
            else:
                updated_storage_text_lv.append("")

        # --- MV Buses ---
        for bus_id in mv_ids:
            # Load data
            P_val = model.P_bus[t, bus_id].value
            Q_val = model.Q_bus[t, bus_id].value
            updated_lbus_mv.append(
                f"MV Bus {bus_id}<br>Load: {P_val:.3f} MW, {Q_val:.3f} MVAR (Timestep {t})"
            )

            # PV/Inverter/Storage (same logic as LV buses)
            if model.PV_surf[bus_id].value > 0.5:
                pv_cap = model.PV_surf[bus_id].value * 1e-3 * 0.2
                updated_pv_text_mv.append(
                    f"PV on MV Bus {bus_id}<br>Capacity: {pv_cap:.3f} MWp (Timestep {t})"
                )
            else:
                updated_pv_text_mv.append("")

            # ... (repeat for inverter/storage, similar to LV buses)


        updated_subs_built_text = []
        updated_subs_not_built_text = []
        updated_slack_built_text = []
        updated_slack_not_built_text = []
        
        # Update slack buses' dynamic info.
        for slack_id, slack in SLACK.items():
            if hasattr(model, "beta"):
                if model.beta[slack_id].value >= 0.8:
                    sub_capacity = model.subs_hv_capacity[slack_id].value
                    sub_power = (model.subs_hv_P[t,slack_id].value**2+model.subs_hv_Q[t,slack_id].value**2)**0.5
                    sub_lin_power = model.subs_hv_S[t,slack_id].value
                    updated_slack_built_text.append(
                        f"Slack {slack_id} (Active)<br>Capacity: {sub_capacity:.3f}<br>Power: {sub_power:.3f}<br>Lin Power: {sub_lin_power:.3f}"
                    )
                else:
                    sub_capacity = model.subs_hv_capacity[slack_id].value
                    sub_power = (model.subs_hv_P[t,slack_id].value**2+model.subs_hv_Q[t,slack_id].value**2)**0.5
                    updated_slack_not_built_text.append(
                        f"Slack {slack_id} (Not Active)<br>Beta: {model.beta[slack_id].value:.3f}<br>Capacity: {sub_capacity:.3f}<br>Power: {sub_power:.3f}"
                    )
        
        # Update line midpoint hover texts.
        new_midpoint_texts = []
        for cond in conductor_order:
            texts = []
            for line_id, line in LINES.items():
                built = False
                if hasattr(model, 'line_act') and model.line_act[line_id].value > 0.8:
                    built = True

                if built:
                    chosen_conductor = None
                    for cond_key in LINES_OPT.keys():
                        if model.line_opt[line_id, cond_key].value > 0.8:
                            chosen_conductor = cond_key
                            break
                    if chosen_conductor is None:
                        chosen_conductor = "unknown"
                else:
                    chosen_conductor = "not_built"
                
                if chosen_conductor == cond:
                    act_p = model.active_power[t, line_id].value if hasattr(model, "active_power") else 0
                    react_p = model.reactive_power[t, line_id].value if hasattr(model, "reactive_power") else 0
                    losses = model.losses[t, line_id].value if hasattr(model, "losses") else 0
                    fict_p = model.fictitious_power[t, line_id].value if hasattr(model, "fictitious_power") else 0
                    texts.append(
                        f"Line {line_id}<br>Length: {line.length}<br>Active: {act_p:.3f} MW<br>"
                        f"Reactive: {react_p:.3f} MVAR<br>Losses: {losses:.3f}<br>Fict: {fict_p:.3f} (Timestep {t})"
                    )
            new_midpoint_texts.append(texts)
        
        # Assemble frame update list.
        # Data order:
        # 0: lbus, 1: subs_built, 2: subs_not_built, 3: slack_built, 4: slack_not_built,
        # 5: PV, 6: inverters, 7: storage, then line traces (for each conductor group: geometry then midpoint).
        frame_updates = [
            {"text": updated_lbus_lv},     # Trace 0: LV buses
            {"text": updated_lbus_mv}, 
            {"text": updated_subs_built_text},
            {"text": updated_subs_not_built_text},
            {"text": updated_slack_built_text},
            {"text": updated_slack_not_built_text},
            {"text": updated_pv_text_lv},
            {"text": updated_pv_text_mv},
            {"text": updated_inv_text_lv},
            {"text": updated_inv_text_mv},
            {"text": updated_storage_text_lv},
            {"text": updated_storage_text_lv}
        ]
        
        for texts in new_midpoint_texts:
            frame_updates.append({})             # geometry trace remains unchanged
            frame_updates.append({"text": texts})  # update midpoint markers
        
        frames.append(go.Frame(data=frame_updates, name=str(t)))
    
    fig.frames = frames

    # ====== ADD SLIDER ======
    slider = dict(
        steps=[dict(
            method="animate",
            args=[[str(t)], 
                  dict(mode="immediate",
                       frame=dict(duration=500, redraw=True),
                       transition=dict(duration=300))],
            label=str(t)
        ) for t in model.periods],
        active=0,
        transition=dict(duration=300),
        currentvalue=dict(prefix="Timestep: ", visible=True, xanchor="center"),
        x=0, y=0, len=1.0
    )
    
    fig.update_layout(
        title="Optimized Distribution Network Solution",
        xaxis_title="X Coordinate",
        yaxis_title="Y Coordinate",
        sliders=[slider],
        hovermode="closest"
    )

    filename = f"Results_{count}.html"
    fig.write_html(filename)
    
    return fig

def check_loads(LBUS):
    for bus_id, bus in LBUS.items():
        # Calculate apparent power and power factor for each time step
        p = bus.load_kW
        q = bus.load_kVAR
        s = [math.sqrt(pi**2 + qi**2) for pi, qi in zip(p, q)]
        power_factor = [pi / si if si != 0 else 0 for pi, si in zip(p, s)]

        voltage_level = bus.voltage_level

        # Create subplots
        fig, axs = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

        # Plot apparent power
        axs[0].plot(s, label='Apparent Power (kVA)')
        axs[0].set_title(f'Bus {bus_id} - Voltage Level: {voltage_level}')
        axs[0].set_ylabel('kVA')
        axs[0].grid(True)

        # Plot power factor
        axs[1].plot(power_factor, label='Power Factor', color='orange')
        axs[1].set_ylabel('Power Factor')
        axs[1].set_xlabel('Time Step')
        axs[1].grid(True)

        plt.tight_layout()
        plt.show()


def write_inv_info_to_csv(inv_infos, filename='inv_info_table.csv', missing_value='NA'):
    """
    Writes inverter information per bus to a CSV file.

    Parameters:
    - inv_infos (dict): Dictionary where keys are bus IDs and values are dicts of inverter info.
    - filename (str): Output CSV file path.
    - missing_value (any): Value to insert for missing keys in some entries.
    """

    # Get all unique field names from all inv_info dictionaries
    all_keys = set()
    for info in inv_infos.values():
        all_keys.update(info.keys())
    all_keys = sorted(all_keys)  # Optional: sort keys for consistent column order

    # Add 'bus_id' as the first column
    fieldnames = ['bus_id'] + all_keys

    with open(filename, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for bus_id, info in inv_infos.items():
            row = {'bus_id': bus_id}
            for key in all_keys:
                row[key] = info.get(key, missing_value)
            writer.writerow(row)

    print(f"Data successfully written to {filename}")
