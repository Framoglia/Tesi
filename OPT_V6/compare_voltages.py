import plotly.graph_objects as go
import math

def plot_voltage_comparison(net, model, pp_bus_map):
    """
    Compares voltage magnitudes from the optimization model with the power flow solution.
    
    Assumptions:
      - The solved pandapower network 'net' has power flow results in net.res_bus,
        with voltage magnitudes in column 'vm_pu' (in per unit).
      - The optimization model 'model' contains voltage magnitudes in a dictionary attribute,
        e.g. model.vm_opt, where keys are the original bus IDs and values are the opt voltages (in p.u.).
      - pp_bus_map is a dictionary mapping the original bus IDs to the pandapower bus indices.
    
    The function creates a scatter plot where each point represents a bus:
      - x-axis: Optimization voltage magnitude (p.u.)
      - y-axis: Power flow voltage magnitude (p.u.)
      
    An identity line is added for reference (if the points lie on it, the voltages are equal).
    """
    
    # Prepare lists to hold data for each bus.
    opt_voltages = []
    pf_voltages = []
    bus_labels   = []
    
    # Iterate over all bus IDs available in the optimization solution.
    for bus_id in model.B:
        if bus_id not in pp_bus_map:
            continue  # Skip if there is no mapping for this bus.
        
        # Get the pandapower bus index.
        pp_bus = pp_bus_map[bus_id]
        try:
            # Get the voltage from the power flow results.
            pf_voltage = net.res_bus.loc[pp_bus, 'vm_pu']
        except KeyError:
            # Skip if the pandapower bus is not found in net.res_bus.
            continue
        
        # Append data.
        opt_voltages.append(math.sqrt(model.voltage_squared[1,bus_id].value))
        pf_voltages.append(pf_voltage)
        bus_labels.append(str(bus_id))
    
    # Create a scatter plot comparing the two voltages.
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=opt_voltages,
        y=pf_voltages,
        mode='markers+text',
        text=bus_labels,
        textposition="top center",
        marker=dict(size=10, color='blue'),
        name='Bus Voltages'
    ))
    
    # Determine range for the identity line.
    all_voltages = opt_voltages + pf_voltages
    vmin = min(all_voltages)
    vmax = max(all_voltages)
    
    # Add identity line (x=y).
    fig.add_trace(go.Scatter(
        x=[vmin, vmax],
        y=[vmin, vmax],
        mode='lines',
        line=dict(dash='dash', color='black'),
        name='Identity Line'
    ))
    
    # Update layout.
    fig.update_layout(
        title="Voltage Magnitude Comparison: Optimization vs Power Flow",
        xaxis_title="Optimization Voltage Magnitude (p.u.)",
        yaxis_title="Power Flow Voltage Magnitude (p.u.)",
        template="plotly_white"
    )
    
    fig.show()
