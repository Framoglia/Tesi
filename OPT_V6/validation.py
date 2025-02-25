import pandapower as pp
import pandas as pd
from pandapower.plotting.plotly import simple_plotly
from pandapower.plotting.plotly import pf_res_plotly



def export_and_solve(model, LBUS, SUBS, SLACK, LINES, LINES_OPT):
    """
    Builds a pandapower network based on the provided data and solved model.
    
    Steps:
      1. For each bus in LBUS: create a pandapower bus (MV level), assign its load, and record geodata.
      2. For each bus in SUBS (substations): if built (gamma > 0.8), create an additional LV bus (stepped down),
         connect the MV and LV buses with an ideal transformer, and store the LV bus id.
      3. For each bus in SLACK: if active (beta > 0.8), create an HV bus (with ext_grid) and its corresponding MV bus,
         connected via an ideal transformer.
      4. For each line: if built (line_act_plus or line_act_minus > 0.8) and with an optimized conductor (line_opt),
         connect the proper bus endpoints – using the LV bus for subs/slacks when appropriate.
      5. Run the power flow.
      6. Assign geodata to the network.
    
    Parameters:
      model      : The solved optimization model with attributes gamma, beta, line_act_plus, line_act_minus, line_opt.
      LBUS       : Dict of load bus objects (each with voltage_level, load_kW, load_kVAR, x_coord, y_coord).
      SUBS       : Dict of substation objects (with voltage_level, x_coord, y_coord).
      SLACK      : Dict of slack bus objects (with voltage_level, x_coord, y_coord).
      LINES      : Dict of line objects (with from_bus, to_bus, length).
      LINES_OPT  : Dict of conductor objects (with r_per_km, xl_per_km, imax_kA).
    
    Returns:
      net : The pandapower network after running a power flow simulation.
    """
    
    net = pp.create_empty_network()

    # Mapping dictionaries for later use:
    pp_bus_map = {}         # For buses created from LBUS (MV buses)
    sub_lv_map = {}         # For substations: mapping substation id -> LV bus id
    slack_mv_map = {}       # For slack nodes: mapping slack id -> MV bus id (the one behind the HV ext_grid)
    geodata = {}            # To store geodata: pandapower bus index -> (x, y)
    
    # 1. Create buses for each LBUS: MV bus, add load, and store geodata.
    for bus_id, bus in LBUS.items():
        # Create the bus at its voltage level (assumed MV)
        pp_bus = pp.create_bus(net, vn_kv=bus.voltage_level/1000, name=f"Bus {bus_id}")
        pp_bus_map[bus_id] = pp_bus
        # Create load immediately
        for t, (p_kw, q_kvar) in enumerate(zip(bus.load_kW, bus.load_kVAR)):
            pp.create_load(net, bus=pp_bus, p_mw=p_kw/1000, q_mvar=q_kvar/1000, name=f"Load {bus_id} T{t}")
        # Store geodata from LBUS
        geodata[pp_bus] = (bus.x_coord, bus.y_coord)
    
    # 2. Process SUBS: For each substation, if built (gamma > 0.8), create an LV bus.
    for sub_id, sub in SUBS.items():
        # Check if built via gamma parameter (if not, skip modifying the bus)
        if not hasattr(model, 'gamma') or model.gamma[sub_id].value < 0.8:
            continue  # not built; leave bus as is.
        
        mv_bus = pp.create_bus(net, vn_kv=sub.voltage_level/1000, name=f"Sub MV {sub_id}")
        pp_bus_map[sub_id] = mv_bus
        geodata[mv_bus] = (sub.x_coord, sub.y_coord)
        # Create an LV bus – place it near the MV bus (offset slightly, e.g., by 0.01)
        lv_bus = pp.create_bus(net, vn_kv=0.4, name=f"Sub LV {sub_id}")
        sub_lv_map[sub_id] = lv_bus
        # Offset coordinates for LV bus (example: add 0.01 to x and subtract 0.01 from y)
        geodata[lv_bus] = (sub.x_coord + 0.5, sub.y_coord - 0.5)
        # Connect MV and LV buses with an ideal transformer (adjust std_type as needed)
        create_ideal_transformer(net, mv_bus, lv_bus, hv_kv=15, lv_kv=0.4, sn_mva=10, name=f"MV/LV Transformer {sub_id}")
    
    # 3. Process SLACK: For each slack, if active (beta > 0.8), create an HV bus and its MV bus.
    for slack_id, slack in SLACK.items():
        if not hasattr(model, 'beta') or model.beta[slack_id].value < 0.8:
            continue  # not active
        # Create an HV bus at slack voltage
        hv_bus = pp.create_bus(net, vn_kv=slack.voltage_level/1000, name=f"Slack HV {slack_id}")
        geodata[hv_bus] = (slack.x_coord, slack.y_coord)

        mv_bus = pp.create_bus(net, vn_kv=15, name=f"Slack MV {slack_id}")
        pp_bus_map[slack_id] = mv_bus
        geodata[mv_bus] = (slack.x_coord + 0.5, slack.y_coord - 0.5)
        slack_mv_map[slack_id] = mv_bus
        # Connect HV and MV with an ideal transformer (adjust std_type as needed)
        create_ideal_transformer(net, hv_bus, mv_bus, hv_kv=40, lv_kv=15, sn_mva=40, name=f"Slack Transformer {slack_id}")
        # Add ext_grid at HV bus
        pp.create_ext_grid(net, bus=hv_bus, vm_pu=1.0, name=f"ExtGrid {slack_id}")
    
    # 4. Create lines.
    # For each line, check if built (line_act_plus or line_act_minus > 0.8) and then determine the proper endpoints.
    for line_id, line in LINES.items():
        # Check built status:
        built = False
        if hasattr(model, 'line_act_plus') and model.line_act_plus[line_id].value > 0.8:
            built = True
        if hasattr(model, 'line_act_minus') and model.line_act_minus[line_id].value > 0.8:
            built = True
        if not built:
            continue  # Skip this line
        
        # Determine optimized conductor parameters:
        chosen = None
        for cond in LINES_OPT.keys():
            if model.line_opt[line_id, cond].value > 0.8:
                chosen = LINES_OPT[cond]
                break
        if chosen is None:
            r_per_km, x_per_km, max_i_ka = 0.1, 0.2, 0.4
        else:
            r_per_km = chosen.r_per_km
            x_per_km = chosen.xl_per_km
            max_i_ka = chosen.imax_kA

        def get_line_connection(line, net):
            """
            Determines the correct pandapower bus indices for a line connection.
            
            Assumptions:
            - Lines connecting two load buses (both in LBUS) use the original bus mapping (pp_bus_map).
            - If one terminal is in SUBS, the function checks the voltage level of the other terminal:
                1) If the other terminal is a SLACK:
                - Use the SUBS MV bus (from sub_mv_map) for the substation side.
                - Use the slack bus (from slack_mv_map) for the slack side.
                2) If the other terminal is in LBUS with voltage == 15 kV:
                - Use the SUBS MV bus (from sub_mv_map) for the substation side.
                3) If the other terminal is in LBUS with voltage == 0.4 kV:
                - Use the SUBS LV bus (from sub_lv_map) for the substation side.
                
            Parameters:
            - line: an object with attributes "from_bus" and "to_bus" (original bus IDs)
            - net: the pandapower network (needed to look up bus voltage levels via net.bus.vn_kv)
            
            Returns:
            A tuple (from_pp_bus, to_pp_bus) with the pandapower bus indices to be used.
            """
            
            # Get default bus indices from the mapping
            from_default = pp_bus_map[line.from_bus]
            to_default   = pp_bus_map[line.to_bus]
            
            # If neither terminal is in SUBS, return defaults.
            if (line.from_bus not in SUBS) and (line.to_bus not in SUBS):
                return from_default, to_default

            # Initialize a flag to determine ordering later.
            order = 0  
            if line.from_bus in SUBS:
                sub_id = line.from_bus
                other_id = line.to_bus
                other_pp_bus = pp_bus_map[other_id]
                other_voltage = net.bus.vn_kv.at[other_pp_bus]
            else:
                order = 1
                sub_id = line.to_bus
                other_id = line.from_bus
                other_pp_bus = pp_bus_map[other_id]
                other_voltage = net.bus.vn_kv.at[other_pp_bus]
            
            # Determine the correct bus for the SUBS terminal.
            if other_id in SLACK:
                # Option 1: Other terminal is a SLACK bus.
                sub_bus = pp_bus_map.get(sub_id, pp_bus_map[sub_id])
                other_bus = slack_mv_map.get(other_id, pp_bus_map[other_id])
            elif other_voltage == 15:
                # Option 2: Other terminal is a load bus with 15 kV.
                sub_bus = pp_bus_map.get(sub_id, pp_bus_map[sub_id])
                other_bus = pp_bus_map[other_id]
            elif other_voltage == 0.4:
                # Option 3: Other terminal is a load bus with 0.4 kV.
                sub_bus = sub_lv_map.get(sub_id, pp_bus_map[sub_id])
                other_bus = pp_bus_map[other_id]
            else:
                # Fallback to default mapping.
                return from_default, to_default

            # Return in the correct order:
            if order == 0:
                return sub_bus, other_bus
            else:
                return other_bus, sub_bus


    
        
        from_pp_bus, to_pp_bus = get_line_connection(line, net)


        pp.create_line_from_parameters(net, from_pp_bus, to_pp_bus, length_km=line.length/100,
                                        r_ohm_per_km=r_per_km, x_ohm_per_km=x_per_km,
                                        c_nf_per_km=0, max_i_ka=max_i_ka,
                                        name=f"Line {line_id}")
    
    # 5. (Optional) If any additional loads or injections need to be re-assigned, they can be processed here.
    
    # 6. Assign geodata to pandapower bus geodata DataFrame.
    # Build a DataFrame from the geodata dictionary.
    geo_df = pd.DataFrame.from_dict(geodata, orient='index', columns=['x', 'y'])
    net.bus_geodata = geo_df
    
    fig = simple_plotly(net)
    fig.show()


    # 7. Run power flow simulation.
    pp.runpp(net)
    fig = pf_res_plotly(net)
    fig.show()
    
    
    return net, pp_bus_map

import pandapower as pp

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


def create_ideal_transformer(net, hv_bus, lv_bus, hv_kv, lv_kv, sn_mva, name):
    """
    Creates an ideal transformer in pandapower with near-zero losses and impedance.

    Parameters:
    - net: pandapower network
    - hv_bus: high-voltage bus index
    - lv_bus: low-voltage bus index
    - hv_kv: high-voltage level in kV
    - lv_kv: low-voltage level in kV
    - sn_mva: rated power in MVA
    - name: transformer name
    """
    pp.create_transformer_from_parameters(
        net, hv_bus=hv_bus, lv_bus=lv_bus,
        sn_mva=sn_mva,  # Rated power
        vn_hv_kv=hv_kv,  # HV side voltage
        vn_lv_kv=lv_kv,  # LV side voltage
        vk_percent=0.01,  # Near-zero short-circuit voltage
        vkr_percent=0.01,  # Near-zero resistance
        pfe_kw=0.01,  # Near-zero iron losses
        i0_percent=0.01,  # Near-zero no-load current
        name=name
    )

