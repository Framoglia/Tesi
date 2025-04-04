import pandapower as pp
import pandas as pd
from pyomo.environ import Var, Param
import math
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

################################################################################################################

def export_optimal_values(model, blacklist=[]):
    """
    Export optimal solution values for variables and parameters not in the blacklist.
    
    For each component (Var/Param) not in the blacklist, this function:
      - Extracts the underlying Pyomo sets (and their names) over which it is indexed.
      - Builds a global ordering of these sets.
      - Creates rows where each row starts with the component name, then contains
        the index values in the order of the global set list (using nan if not defined),
        and ends with the variable/parameter value.
      - Exports the result as a CSV file whose header includes the set names.
    
    Parameters:
      model     : The Pyomo model
      filename   : A string to uniquely identify the CSV filename.
      blacklist : A list of component names (as strings) to ignore.
    """
    
    filename = f"optimal_values.csv"
    rows = []           # List of rows to write out.
    global_sets = []    # Global ordered list of all set names used.
    comp_set_map = {}   # Mapping: component name -> ordered list of set names used for its indexing.

    # Collect both Var and Param components (not in the blacklist)
    components = list(model.component_objects(Var, active=True)) + list(model.component_objects(Param, active=True))
    
    # FIRST PASS: Determine the sets over which each component is defined
    for comp in components:
        comp_name = comp.local_name
        if comp_name in blacklist:
            continue
        
        # If the component is indexed, try to extract its index set tuple.
        if comp.is_indexed():
            try:
                # For multi-indexed components, index_set() returns a product with an attribute 'set_tuple'
                idx_tuple = comp.index_set().subsets(expand_all_set_operators=False)
            except AttributeError:
                # If not a product, treat as a one-element tuple.
                idx_tuple = (comp.index_set(),)
            idx_names = []
            for s in idx_tuple:
                try:
                    set_name = s.local_name  # Use the set's local name if available.
                except AttributeError:
                    set_name = str(s)
                idx_names.append(set_name)
                if set_name not in global_sets:
                    global_sets.append(set_name)
        else:
            idx_names = []
            
        comp_set_map[comp_name] = idx_names
    
    # SECOND PASS: Build the rows for each component using the global ordering of sets.
    # Process Var components
    for comp in model.component_objects(Var, active=True):
        comp_name = comp.local_name
        if comp_name in blacklist:
            continue
        
        idx_names = comp_set_map.get(comp_name, [])
        if comp.is_indexed():
            for index in comp:
                value = comp[index].value
                # Ensure index is a tuple
                index_tuple = index if isinstance(index, tuple) else (index,)
                # Build row: start with name, then one entry per global set, then the value.
                row = [comp_name]
                for set_name in global_sets:
                    if set_name in idx_names:
                        pos = idx_names.index(set_name)
                        # Use the index value if available; else fill with nan.
                        row.append(index_tuple[pos] if pos < len(index_tuple) else float('nan'))
                    else:
                        row.append(float('nan'))
                row.append(value)
                rows.append(row)
        else:
            # Scalar variable: no indices; fill with nans for set columns.
            value = comp.value
            row = [comp_name] + [float('nan')] * len(global_sets) + [value]
            rows.append(row)
    
    # Process Param components (similar to Var components)
    for comp in model.component_objects(Param, active=True):
        comp_name = comp.local_name
        if comp_name in blacklist:
            continue
        
        idx_names = comp_set_map.get(comp_name, [])
        if comp.is_indexed():
            for index in comp:
                value = comp[index].value
                index_tuple = index if isinstance(index, tuple) else (index,)
                row = [comp_name]
                for set_name in global_sets:
                    if set_name in idx_names:
                        pos = idx_names.index(set_name)
                        row.append(index_tuple[pos] if pos < len(index_tuple) else float('nan'))
                    else:
                        row.append(float('nan'))
                row.append(value)
                rows.append(row)
        else:
            value = comp.value
            row = [comp_name] + [float('nan')] * len(global_sets) + [value]
            rows.append(row)
    
    # Build header: first column is 'Name', then one column for each global set, then 'Value'.
    header = ["Name"] + global_sets + ["Value"]
    
    # Create DataFrame and export to CSV
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
        name = f"comparison_t{t}.png"
        plt.savefig(name, dpi=300, bbox_inches='tight')

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


    return esperiment

################################################################################################################

def precision(esperiment):
    x,y = esperiment
    return (sum(i for i in x) - sum(i for i in y)) / sum(i for i in y) * 100

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

def move_files_to_folder(folder_name = 'organized_files'):

    folder_name = folder_name + '_' + datetime.now().strftime("%d_%m_%H_%M")
    
    # Create the folder if it doesn't exist
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    # Find all .png and .csv files in the current directory
    png_files = glob.glob('*.png')
    csv_files = glob.glob('*.csv')
    txt_files = glob.glob('*.txt')
    log_files = glob.glob('*.log')
    lp_files = glob.glob('*.lp')
    pkl_files = glob.glob('*.pkl')
    html_files = glob.glob('*.html')
    
    # Move .png files to the new folder
    for file in png_files:
        shutil.move(file, os.path.join(folder_name, file))
    
    # Move .csv files to the new folder
    for file in csv_files:
        shutil.move(file, os.path.join(folder_name, file))

    # Move .txt files to the new folder
    for file in txt_files:
        shutil.move(file, os.path.join(folder_name, file))

    # Move .log files to the new folder
    for file in log_files:
        shutil.move(file, os.path.join(folder_name, file))

    # Move .lp files to the new folder
    for file in lp_files:
        shutil.move(file, os.path.join(folder_name, file))

    # Move .pkl files to the new folder
    for file in pkl_files:
        shutil.move(file, os.path.join(folder_name, file))

    # Move .html files to the new folder
    for file in html_files:
        shutil.move(file, os.path.join(folder_name, file))
    
    print(f"Moved files to '{folder_name}'.")

################################################################################################################

def plot_network_solution(model, LBUS, SUBS, SLACK, LINES, LINES_OPT):
    """
    Creates an interactive Plotly figure of the optimized distribution network.
    
    Parameters:
      model      : The solved optimization model. It must contain:
                     - model.periods: an iterable of timesteps.
                     - For each load bus: model.P_bus[t, bus_id].value, model.Q_bus[t, bus_id].value.
                     - Investment decisions per bus: model.PV_surf[bus_id].value and model.S_inv[bus_id].value.
                     - For substations: model.gamma[sub_id].value (built if >=0.8).
                     - For slack buses: model.beta[slack_id].value (active if >=0.8).
                     - For each line: model.line_act_plus[line_id].value or model.line_act_minus[line_id].value (built if > 0.8)
                     - For each line: model.line_opt[line_id, cond].value for each conductor type.
                     - For each line (per timestep): model.active_power[t, line_id].value,
                       model.reactive_power[t, line_id].value, model.losses[t, line_id].value,
                       and model.fictitious_power[t, line_id].value.
      LBUS       : Dict of load bus objects with attributes: voltage_level, x_coord, y_coord, and surface.
      SUBS       : Dict of substation objects with attributes: voltage_level, x_coord, y_coord.
      SLACK      : Dict of slack bus objects with attributes: voltage_level, x_coord, y_coord.
      LINES      : Dict of line objects with attributes: from_bus, to_bus, length.
      LINES_OPT  : Dict of conductor objects (keyed by conductor type) with attributes: r_per_km, xl_per_km, imax_kA.
    
    Returns:
      fig        : A Plotly figure with a timestep slider and update buttons to toggle visibility of not built lines
                   and not built substations/slack.
    """
    import plotly.graph_objects as go

    # ====== Configuration ======
    bus_type_info = {
        "LBUS":  {"color": "blue",   "symbol": "circle",   "name": "Load Bus"},
        "SUBS":  {"color": "red",    "symbol": "square",   "name": "Substation"},
        "SLACK": {"color": "green",  "symbol": "diamond",  "name": "Slack"}
    }
    not_built_color = "grey"
    
    # Investment markers (offset relative to bus)
    pv_symbol  = "star"
    inv_symbol = "x"
    pv_offset  = (5, 5)
    inv_offset = (2.5, 2.5)
    
    # Conductor colors
    conductor_colors = {
        "Poppy": "#90E0EF",
        "Oxlip": "#00B4D8",
        "Daisy": "#0077B6",
        "Tulip": "#03045E"
    }
    
    # ====== Build Bus, Substation, Slack & Investment Traces ======
    # -- Load Buses (LBUS)
    lbus_ids, lbus_x, lbus_y, lbus_text = [], [], [], []
    t0 = next(iter(model.periods))
    for bus_id, bus in LBUS.items():
        lbus_ids.append(bus_id)
        lbus_x.append(bus.x_coord)
        lbus_y.append(bus.y_coord)
        P0 = model.P_bus[t0, bus_id].value
        Q0 = model.Q_bus[t0, bus_id].value
        lbus_text.append(f"Bus {bus_id}<br>Load: {P0:.3f} MW, {Q0:.3f} MVAR")
    
    lbus_trace = go.Scatter(
        x=lbus_x, y=lbus_y,
        mode="markers",
        marker=dict(color=bus_type_info["LBUS"]["color"],
                    symbol=bus_type_info["LBUS"]["symbol"],
                    size=10),
        text=lbus_text,
        hoverinfo="text",
        name=bus_type_info["LBUS"]["name"]
    )
    
    # -- Substations (SUBS)
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
    
    # -- Slack Buses (SLACK)
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
    
    # -- Investment markers (PV and Inverter)
    pv_x, pv_y, pv_text = [], [], []
    inv_x, inv_y, inv_text = [], [], []
    for bus_id, bus in LBUS.items():
        if model.PV_surf[bus_id].value > 0.5:
            pv_x.append(bus.x_coord + pv_offset[0])
            pv_y.append(bus.y_coord + pv_offset[1])
            pv_text.append(f"PV installed on Bus {bus_id}")
        if model.S_inv[bus_id].value > 0.0005:
            inv_x.append(bus.x_coord + inv_offset[0])
            inv_y.append(bus.y_coord + inv_offset[1])
            inv_text.append(f"Inverter installed on Bus {bus_id}")
    
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
    
    # ====== Build Line Traces (Geometry and Midpoint Markers) ======
    # First, build a mapping of bus id to coordinates.
    bus_coords = {bus_id: (bus.x_coord, bus.y_coord) for bus_id, bus in LBUS.items()}
    bus_coords.update({sub_id: (sub.x_coord, sub.y_coord) for sub_id, sub in SUBS.items()})
    bus_coords.update({slack_id: (slack.x_coord, slack.y_coord) for slack_id, slack in SLACK.items()})
    
    # For each line, compute:
    #   - The endpoints (for drawing the line)
    #   - The midpoint (for the hover marker)
    # Group lines by conductor (or "not_built")
    lines_geom_by_conductor = {}   # For geometry (no hover text)
    midpoints_by_conductor = {}      # For midpoints (with hover text)
    conductor_order = []
    
    # Use t0 for initial hover text on lines.
    for line_id, line in LINES.items():
        built = False
        if hasattr(model, "line_act_plus") and model.line_act_plus[line_id].value > 0.8:
            built = True
        if hasattr(model, "line_act_minus") and model.line_act_minus[line_id].value > 0.8:
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
            # Compute midpoint
            xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
            
            # Prepare initial hover text using t0
            act_p = model.active_power[t0, line_id].value if hasattr(model, "active_power") else 0
            react_p = model.reactive_power[t0, line_id].value if hasattr(model, "reactive_power") else 0
            losses = model.losses[t0, line_id].value if hasattr(model, "losses") else 0
            fict_p = model.fictitious_power[t0, line_id].value if hasattr(model, "fictitious_power") else 0
            
            line_hover = (f"Line {line_id}<br>Length: {line.length}<br>"
                          f"Active Power: {act_p:.3f} MW<br>"
                          f"Reactive Power: {react_p:.3f} MVAR<br>"
                          f"Losses: {losses:.3f}<br>"
                          f"Fictitious Power: {fict_p:.3f}")
            
            # Append endpoints for geometry (we add a break with None)
            if chosen_conductor not in lines_geom_by_conductor:
                lines_geom_by_conductor[chosen_conductor] = {"x": [], "y": []}
                midpoints_by_conductor[chosen_conductor] = {"x": [], "y": [], "text": []}
                conductor_order.append(chosen_conductor)
            lines_geom_by_conductor[chosen_conductor]["x"].extend([x0, x1, None])
            lines_geom_by_conductor[chosen_conductor]["y"].extend([y0, y1, None])
            # For midpoints, add one marker per line.
            midpoints_by_conductor[chosen_conductor]["x"].append(xm)
            midpoints_by_conductor[chosen_conductor]["y"].append(ym)
            midpoints_by_conductor[chosen_conductor]["text"].append(line_hover)
    
    # Now create two traces per conductor group:
    # (a) The geometry trace (static) and (b) The midpoint marker trace (with hover info).
    line_traces = []
    midpoint_trace_indices = []  # To track the order for frame updates.
    for cond in conductor_order:
        # Geometry trace: drawn as lines.
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
        # Midpoint marker trace: points with hover text.
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
        midpoint_trace_indices.append(midpoint_trace)  # save reference for updating frames
    
    # ====== Assemble the Figure ======
    # Data order: buses, substations, slack, investments, then line traces (geometry and midpoints).
    data = [
        lbus_trace,
        subs_built_trace,
        subs_not_built_trace,
        slack_built_trace,
        slack_not_built_trace,
        pv_trace,
        inv_trace
    ] + line_traces

    fig = go.Figure(data=data)
    
    # ====== Build Frames for Timestep Slider ======
    frames = []
    for t in model.periods:
        new_lbus_text = []  # Updated bus hover text
        new_pv_text   = []  # Updated PV hover text
        new_inv_text  = []  # Updated inverter hover text
        
        # Update bus, PV, inverter texts.
        for bus_id in lbus_ids:
            P_val = model.P_bus[t, bus_id].value
            Q_val = model.Q_bus[t, bus_id].value 
            bus_hover = f"Bus {bus_id}<br>Load: {P_val:.3f} MW, {Q_val:.3f} MVAR (Timestep {t})"
            new_lbus_text.append(bus_hover)
            
            if model.S_inv[bus_id].value > 0.0005:
                inv_cap = model.S_inv[bus_id].value
                inv_usage = model.S_sun[t, bus_id].value / inv_cap if inv_cap != 0 else 0
                inv_hover = (f"Inverter on Bus {bus_id}<br>Capacity: {inv_cap:.3f} MVAR<br>"
                             f"Usage: {inv_usage*100:.0f} %")
            else:
                inv_hover = ""
            new_inv_text.append(inv_hover)
            
            if model.PV_surf[bus_id].value > 0.5:
                pv_cap = model.PV_surf[bus_id].value * 1e-3 * 0.2 
                installed_fraction = model.PV_surf[bus_id].value / LBUS[bus_id].surface if LBUS[bus_id].surface != 0 else 0
                pv_usage = model.S_sun[t, bus_id].value
                pv_hover = (f"PV on Bus {bus_id}<br>Capacity: {pv_cap:.3f} MWp<br>"
                            f"Installed Fraction: {installed_fraction*100:.0f} %<br>"
                            f"Production: {pv_usage:.3f} MW")
            else:
                pv_hover = ""
            new_pv_text.append(pv_hover)
        
        # --- Update line midpoint hover texts dynamically ---
        # For each conductor group, rebuild the hover text for each line.
        new_midpoint_texts = []  # Order corresponds to the midpoint marker traces in our figure.
        for cond in conductor_order:
            texts = []
            # Retrieve the list of lines (midpoints) for this group.
            # We need to loop over each line in LINES that belongs to this group.
            for line_id, line in LINES.items():
                built = False
                if hasattr(model, "line_act_plus") and model.line_act_plus[line_id].value > 0.8:
                    built = True
                if hasattr(model, "line_act_minus") and model.line_act_minus[line_id].value > 0.8:
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
                    
                    line_hover = (f"Line {line_id}<br>Length: {line.length}<br>"
                                  f"Active Power: {act_p:.3f} MW<br>"
                                  f"Reactive Power: {react_p:.3f} MVAR<br>"
                                  f"Losses: {losses:.3f}<br>"
                                  f"Fictitious Power: {fict_p:.3f}")
                    texts.append(line_hover)
            # Join all hover texts for this conductor group (each marker corresponds to one line).
            new_midpoint_texts.append(texts)
        
        # Build frame update list:
        # The first 7 traces are for buses, substations, slack, PV, and inverters.
        frame_updates = [
            {"text": new_lbus_text},  # index 0: lbus
            {},  # index 1: subs_built (static)
            {},  # index 2: subs_not_built (static)
            {},  # index 3: slack_built (static)
            {},  # index 4: slack_not_built (static)
            {"text": new_pv_text},   # index 5: pv
            {"text": new_inv_text}   # index 6: inverters
        ]
        # Now, for each conductor group we have two traces (geometry and midpoint). Geometry traces (even indices) remain unchanged.
        # For the midpoint marker traces (odd indices in each group), update the text.
        # Our line_traces order starts at index 7.
        for i, texts in enumerate(new_midpoint_texts):
            # For each conductor group, the geometry trace is at even index and the midpoint marker is at the next index.
            # So we add an empty update for the geometry trace, then update the midpoint marker trace.
            frame_updates.append({})  # Geometry trace update: nothing changes.
            frame_updates.append({"text": texts})  # Midpoint marker trace update.
        
        frame = go.Frame(
            data=frame_updates,
            name=str(t)
        )
        frames.append(frame)
    
    fig.frames = frames

    # ====== Add Slider for Timesteps ======
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

    filename = "Results.html"
    fig.write_html(filename)

    return fig

################################################################################################################

def plot_network_solution_2(model, LBUS, SUBS, SLACK, LINES, LINES_OPT):
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
        "LBUS":  {"color": "blue",   "symbol": "circle",   "name": "Load Bus"},
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
    lbus_ids, lbus_x, lbus_y = [], [], []
    for bus_id, bus in LBUS.items():
        lbus_ids.append(bus_id)
        lbus_x.append(bus.x_coord)
        lbus_y.append(bus.y_coord)
    lbus_trace = go.Scatter(
        x=lbus_x, y=lbus_y,
        mode="markers",
        marker=dict(color=bus_type_info["LBUS"]["color"],
                    symbol=bus_type_info["LBUS"]["symbol"],
                    size=10),
        text=[f"Bus {bus_id}" for bus_id in lbus_ids],
        hoverinfo="text",
        name=bus_type_info["LBUS"]["name"]
    )
    
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
            pv_text.append("")
        # Inverter installation check
        if model.S_inv[bus_id].value > 0.0005:
            inv_x.append(bus.x_coord + inv_offset[0])
            inv_y.append(bus.y_coord + inv_offset[1])
            inv_text.append(f"Inverter installed on Bus {bus_id}")
        else:
            inv_text.append("")
        # Storage investment check
        if hasattr(model, "storage_capacity") and model.storage_capacity[bus_id].value > 0.0005:
            storage_x.append(bus.x_coord + storage_offset[0])
            storage_y.append(bus.y_coord + storage_offset[1])
            storage_text.append(f"Storage installed on Bus {bus_id}")
        else:
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
        if hasattr(model, "line_act_plus") and model.line_act_plus[line_id].value > 0.8:
            built = True
        if hasattr(model, "line_act_minus") and model.line_act_minus[line_id].value > 0.8:
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
        lbus_trace,
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
        updated_lbus_text = []
        updated_subs_built_text = []
        updated_subs_not_built_text = []
        updated_slack_built_text = []
        updated_slack_not_built_text = []
        updated_pv_text = []
        updated_inv_text = []
        updated_storage_text = []
        
        # Update load buses.
        for bus_id in lbus_ids:
            P_val = model.P_bus[t, bus_id].value
            Q_val = model.Q_bus[t, bus_id].value 
            updated_lbus_text.append(
                f"Bus {bus_id}<br>Load: {P_val:.3f} MW, {Q_val:.3f} MVAR (Timestep {t})"
            )
            
            # Inverter dynamic info.
            if model.S_inv[bus_id].value > 0.0005:
                inv_cap = model.S_inv[bus_id].value
                inv_usage = model.S_sun[t, bus_id].value / inv_cap if inv_cap != 0 else 0
                updated_inv_text.append(
                    f"Inverter on Bus {bus_id}<br>Capacity: {inv_cap:.3f} MVAR<br>Usage: {inv_usage*100:.0f}% (Timestep {t})"
                )
            else:
                updated_inv_text.append("")
            
            # PV dynamic info.
            if model.PV_surf[bus_id].value > 0.5:
                pv_cap = model.PV_surf[bus_id].value * 1e-3 * 0.2 
                installed_fraction = model.PV_surf[bus_id].value / LBUS[bus_id].surface if LBUS[bus_id].surface != 0 else 0
                pv_usage = model.S_sun[t, bus_id].value
                updated_pv_text.append(
                    f"PV on Bus {bus_id}<br>Capacity: {pv_cap:.3f} MWp<br>Installed: {installed_fraction*100:.0f}%<br>Prod: {pv_usage:.3f} MW (Timestep {t})"
                )
            else:
                updated_pv_text.append("")
            
            # Storage dynamic info.
            if hasattr(model, "storage_capacity") and model.storage_capacity[bus_id].value > 0.0005:
                storage_capacity = model.storage_capacity[bus_id].value
                storage_power = model.storage_power[bus_id].value 
                storage_transf = (model.P_storage[t, bus_id].value**2 + model.Q_storage[t, bus_id].value**2)**0.5
                storage_soc = model.storage_energy[t, bus_id].value / model.storage_capacity[bus_id].value *100
                updated_storage_text.append(
                    f"Storage on Bus {bus_id}<br>Capacity: {storage_capacity:.3f}<br>Maximum power: {storage_power:.3f}<br>Power: {storage_transf:.3f}<br>SOC: {storage_soc:.1f}"
                )
            else:
                updated_storage_text.append("")
        
        # Update substations' dynamic info.
        for sub_id, sub in SUBS.items():
            if hasattr(model, "gamma"):
                if model.gamma[sub_id].value >= 0.8:
                    sub_capacity = model.subs_mv_capacity[sub_id].value
                    sub_power = (model.subs_mv_P[t,sub_id].value**2+model.subs_mv_P[t,sub_id].value**2)**0.5
                    sub_lin_power = model.subs_mv_S[t,sub_id].value
                    updated_subs_built_text.append(
                        f"Substation {sub_id} (Built)<br>Capacity: {sub_capacity:.3f}<br>Power: {sub_power:.3f}<br>Lin Power: {sub_lin_power:.3f}"
                    )
                else:
                    sub_capacity = model.subs_mv_capacity[sub_id].value
                    sub_power = (model.subs_mv_P[t,sub_id].value**2+model.subs_mv_P[t,sub_id].value**2)**0.5
                    updated_subs_not_built_text.append(
                        f"Substation {sub_id} (Not Built)<br>Gamma: {model.gamma[sub_id].value:.3f}<br>Capacity: {sub_capacity:.3f}<br>Power: {sub_power:.3f}"
                    )
        
        # Update slack buses' dynamic info.
        for slack_id, slack in SLACK.items():
            if hasattr(model, "beta"):
                if model.beta[slack_id].value >= 0.8:
                    sub_capacity = model.subs_hv_capacity[slack_id].value
                    sub_power = (model.subs_hv_P[t,slack_id].value**2+model.subs_hv_P[t,slack_id].value**2)**0.5
                    sub_lin_power = model.subs_hv_S[t,slack_id].value
                    updated_slack_built_text.append(
                        f"Slack {slack_id} (Active)<br>Capacity: {sub_capacity:.3f}<br>Power: {sub_power:.3f}<br>Lin Power: {sub_lin_power:.3f}"
                    )
                else:
                    sub_capacity = model.subs_hv_capacity[slack_id].value
                    sub_power = (model.subs_hv_P[t,slack_id].value**2+model.subs_hv_P[t,slack_id].value**2)**0.5
                    updated_slack_not_built_text.append(
                        f"Slack {slack_id} (Not Active)<br>Beta: {model.beta[slack_id].value:.3f}<br>Capacity: {sub_capacity:.3f}<br>Power: {sub_power:.3f}"
                    )
        
        # Update line midpoint hover texts.
        new_midpoint_texts = []
        for cond in conductor_order:
            texts = []
            for line_id, line in LINES.items():
                built = False
                if hasattr(model, "line_act_plus") and model.line_act_plus[line_id].value > 0.8:
                    built = True
                if hasattr(model, "line_act_minus") and model.line_act_minus[line_id].value > 0.8:
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
            {"text": updated_lbus_text},
            {"text": updated_subs_built_text},
            {"text": updated_subs_not_built_text},
            {"text": updated_slack_built_text},
            {"text": updated_slack_not_built_text},
            {"text": updated_pv_text},
            {"text": updated_inv_text},
            {"text": updated_storage_text}
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

    filename = "Results.html"
    fig.write_html(filename)
    
    return fig
