import math
import plotly.graph_objects as go
from utils import *

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
            pf_current = res["line"].loc[pp_line, 'i_ka'] * 1000  # Convert kA to A
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
