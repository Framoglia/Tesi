import math
import plotly.graph_objects as go
from utils import *

    
def plot_comparisons(net, results, model, pp_bus_map):
    """
    Plots voltage magnitude comparison for each timestep between the optimization model and power flow results.
    
    Parameters:
        results    : Dictionary containing power flow results for each timestep.
        model      : The optimization model containing voltage values.
        pp_bus_map : Mapping from original bus IDs to pandapower bus indices.
    """
    for t, res in results.items():
        if res == "Power flow did not converge":
            continue

        # Prepare voltage comparison data
        opt_voltages = []
        pf_voltages = []
        bus_labels = []
        
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
        
        # Prepare line current and power loss comparison
        opt_currents = []
        pf_currents = []
        opt_losses = []
        pf_losses = []
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

        
        # Create subplots
        fig = go.Figure()
        
        # Voltage comparison
        fig.add_trace(go.Scatter(
            x=opt_voltages, y=pf_voltages, mode='markers+text',
            text=bus_labels, textposition="top center",
            marker=dict(size=10, color='blue'),
            name='Bus Voltages'
        ))
        
        # Current comparison
        fig.add_trace(go.Scatter(
            x=opt_currents, y=pf_currents, mode='markers+text',
            text=line_labels, textposition="top center",
            marker=dict(size=10, color='red'),
            name='Line Currents'
        ))
        
        # Power loss comparison
        fig.add_trace(go.Scatter(
            x=opt_losses, y=pf_losses, mode='markers+text',
            text=line_labels, textposition="top center",
            marker=dict(size=10, color='green'),
            name='Power Losses'
        ))
        
        fig.update_layout(
            title=f"Comparison at Timestep {t+1}",
            xaxis_title="Optimization (p.u.)",
            yaxis_title="Power Flow (p.u.)",
            template="plotly_white"
        )
        fig.show()