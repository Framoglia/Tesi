import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import csv
from collections import defaultdict
from param import *
import seaborn as sns
from utils import BASE_POWER

def cost_check(csv_path):
    # Load data
    df = pd.read_csv(csv_path)
    df = df.set_index('Name')
    # --- CAPEX components ---
    capex_items = {
        'Conductor': df.loc['C_cond', 'Value'],
        'hv Substation': df.loc['C_subs_hv', 'Value'] + df.loc['subs_hv_inst_cost', 'Value'],
        'mv Substation': df.loc['C_subs_mv', 'Value'] + df.loc['subs_mv_inst_cost', 'Value'],
        'PV': df.loc['C_PV', 'Value'] + df.loc['C_inv', 'Value'] + df.loc['PV_inst_cost', 'Value'],
        'Storage': df.loc['C_storage_capacity', 'Value'] + df.loc['storage_inst_cost', 'Value'],
    }
    capex_annualized = {k: v / INV_HORIZON_DSO for k, v in capex_items.items()}

    # --- OPEX components ---
    opex = {
        'Electricity': df.loc['total_C_electricity', 'Value'],
        'Losses': df.loc['total_C_losses', 'Value']
    }

    # --- Pie 1: CAPEX vs OPEX ---
    total_capex = sum(capex_annualized.values())
    total_opex = sum(opex.values())
    pie1_labels = ['CAPEX', 'OPEX']
    pie1_sizes = [total_capex, total_opex]
    pie1_colors = [cm.Paired(0), cm.Paired(1)]

    # --- Pie 2: OPEX Breakdown ---
    pie2_labels = list(opex.keys())
    pie2_sizes = list(opex.values())
    pie2_colors = [cm.Paired(2), cm.Paired(3)]

    # --- Pie 3: Technology Share of CAPEX ---
    pie3_labels = list(capex_annualized.keys())
    pie3_sizes = list(capex_annualized.values())
    pie3_colors = [cm.tab10(i) for i in range(len(pie3_labels))]

    # --- Pie 4: Fixed vs Variable (annualized CAPEX) ---
    fixed_cost = sum([
        df.loc['subs_hv_inst_cost', 'Value'],
        df.loc['subs_mv_inst_cost', 'Value'],
        df.loc['PV_inst_cost', 'Value'],
        df.loc['storage_inst_cost', 'Value'],
    ]) / INV_HORIZON_DSO

    variable_cost = sum([
        df.loc['C_cond', 'Value'],
        df.loc['C_subs_hv', 'Value'],
        df.loc['C_subs_mv', 'Value'],
        df.loc['C_PV', 'Value'],
        df.loc['C_inv', 'Value'],
        df.loc['C_storage_capacity', 'Value'],
    ]) / INV_HORIZON_DSO

    pie4_labels = ['Fixed (Installation)', 'Variable (Capacity/Power/Inverter)']
    pie4_sizes = [fixed_cost, variable_cost]
    pie4_colors = [cm.Paired(4), cm.Paired(5)]

    # --- Plotting ---
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))

    # Pie 1
    axs[0, 0].pie(pie1_sizes, labels=pie1_labels, autopct='%1.1f%%',
                startangle=140, colors=pie1_colors, textprops={'fontsize': 12})
    axs[0, 0].axis('equal')
    axs[0, 0].set_title('Yearly Cost: CAPEX vs OPEX')

    # Pie 2
    axs[0, 1].pie(pie2_sizes, labels=pie2_labels, autopct='%1.1f%%',
                startangle=90, colors=pie2_colors, textprops={'fontsize': 12})
    axs[0, 1].axis('equal')
    axs[0, 1].set_title('OPEX Breakdown')

    # Pie 3
    axs[1, 0].pie(pie3_sizes, labels=pie3_labels, autopct='%1.1f%%',
                startangle=90, colors=pie3_colors, textprops={'fontsize': 10})
    axs[1, 0].axis('equal')
    axs[1, 0].set_title('Annualized CAPEX Breakdown by Technology')

    # Pie 4
    axs[1, 1].pie(pie4_sizes, labels=pie4_labels, autopct='%1.1f%%',
                startangle=90, colors=pie4_colors, textprops={'fontsize': 11})
    axs[1, 1].axis('equal')
    axs[1, 1].set_title('CAPEX: Fixed vs Variable Costs')

    plt.tight_layout()
    plt.show()

import plotly.graph_objects as go
import pandas as pd

import plotly.graph_objects as go
import pandas as pd

def sankey_cost_check(csv_path, inv_horizon_dso=INV_HORIZON_DSO):
    # Load data
    df = pd.read_csv(csv_path)
    df = df.set_index('Name')
    
    # --- Calculate all cost components ---
    # CAPEX components
    capex = {
        'Conductor': df.loc['C_cond', 'Value'],
        'HV Substation': df.loc['C_subs_hv', 'Value'] + df.loc['subs_hv_inst_cost', 'Value'],
        'MV Substation': df.loc['C_subs_mv', 'Value'] + df.loc['subs_mv_inst_cost', 'Value'],
        'PV System': df.loc['C_PV', 'Value'] + df.loc['PV_inst_cost', 'Value'],
        'Storage': df.loc['C_storage_capacity', 'Value'] + df.loc['storage_inst_cost', 'Value'],
        'Inverter': df.loc['C_inv', 'Value'],
    }
    
    # Annualize DSO CAPEX
    dso_capex_annual = {k: v / inv_horizon_dso 
                        for k, v in capex.items() 
                        if k in ['Conductor', 'HV Substation', 'MV Substation']}
    
    # Household CAPEX (not annualized)
    household_capex = {k: v / inv_horizon_dso  for k, v in capex.items() 
                       if k in ['PV System', 'Storage', 'Inverter']}
    
    # OPEX components
    opex = {
        'Electricity': df.loc['C_electricity', 'Value'].sum(),
        'Losses': df.loc['C_losses', 'Value'].sum()
    }
    
    # --- Sankey Diagram Structure ---
    # Nodes ordered from left (level 1) to right (level 4)
    labels = [
        # Level 1: Total (leftmost)
        'Total System Cost',
        
        # Level 2: Aggregates
        'Household Total', 'DSO Total',
        
        # Level 3: CAPEX/OPEX
        'Household CAPEX', 'Household OPEX',
        'DSO CAPEX', 'DSO OPEX',
        
        # Level 4: Technologies (rightmost)
        'PV System', 'Storage', 'Inverter',  # Household
        'HV Substation', 'MV Substation', 'Conductor',  # DSO
        'Electricity', 'Losses'  # OPEX sources
    ]
    
    # Node positions (x-axis from 0 to 1, left to right)
    node_x = [
        0.1,    # Level 1
        0.3, 0.3,  # Level 2
        0.6, 0.6, 0.6, 0.6,  # Level 3
        1, 1, 1, 1, 1, 1, 1, 1  # Level 4
    ]
    
    # Node vertical positions (y-axis)
    node_y = [
        0.5,   # Total
        0.3, 0.7,  # Household Total, DSO Total
        0.2, 0.4,  # Household CAPEX, OPEX
        0.6, 0.8,  # DSO CAPEX, OPEX
        0.1, 0.2, 0.3,  # PV, Storage, Inverter
        0.6, 0.7, 0.8,  # HV, MV, Conductor
        0.4, 0.8   # Electricity, Losses
    ]
    
    # Define all flows (source -> target)
    sources = []
    targets = []
    values = []
    
    # Level 4 -> Level 3 flows
    # Household technologies -> Household CAPEX
    for tech in ['PV System', 'Storage', 'Inverter']:
        sources.append(labels.index(tech))
        targets.append(labels.index('Household CAPEX'))
        values.append(household_capex[tech])
    
    # DSO technologies -> DSO CAPEX
    for tech in ['HV Substation', 'MV Substation', 'Conductor']:
        sources.append(labels.index(tech))
        targets.append(labels.index('DSO CAPEX'))
        values.append(dso_capex_annual[tech])
    
    # OPEX sources -> OPEX categories
    sources.append(labels.index('Electricity'))
    targets.append(labels.index('Household OPEX'))
    values.append(opex['Electricity'])
    
    sources.append(labels.index('Losses'))
    targets.append(labels.append('DSO OPEX'))
    values.append(opex['Losses'])
    
    # Level 3 -> Level 2 flows
    # Household
    household_capex_total = sum(household_capex.values())
    sources.append(labels.index('Household CAPEX'))
    targets.append(labels.index('Household Total'))
    values.append(household_capex_total)
    
    sources.append(labels.index('Household OPEX'))
    targets.append(labels.index('Household Total'))
    values.append(opex['Electricity'])
    
    # DSO
    dso_capex_total = sum(dso_capex_annual.values())
    sources.append(labels.index('DSO CAPEX'))
    targets.append(labels.index('DSO Total'))
    values.append(dso_capex_total)
    
    sources.append(labels.index('DSO OPEX'))
    targets.append(labels.index('DSO Total'))
    values.append(opex['Losses'])
    
    # Level 2 -> Level 1 flows
    sources.append(labels.index('Household Total'))
    targets.append(labels.index('Total System Cost'))
    values.append(household_capex_total + opex['Electricity'])
    
    sources.append(labels.index('DSO Total'))
    targets.append(labels.index('Total System Cost'))
    values.append(dso_capex_total + opex['Losses'])
    
    # --- Create Sankey Diagram ---
    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(
            pad=30,
            thickness=15,
            line=dict(color="black", width=0.5),
            label=labels,
            x=node_x,
            y=node_y,
            color=["#1f77b4"]*len(labels)  # Base color
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=["rgba(31, 119, 180, 0.5)" for _ in values]
        )
    ))
    
    fig.update_layout(
        title_text="System Cost Breakdown (Annual)",
        font_size=12,
        width=1000,
        height=600,
        margin=dict(l=50, r=50, b=50, t=50)
    )
    try:
        fig.show()
    except UnicodeEncodeError as e:
        print("UnicodeEncodeError encountered while displaying the Sankey diagram. Attempting to save as HTML instead.")
        fig.write_html("sankey_cost_check_output.html")
        print("Sankey diagram saved as 'sankey_cost_check_output.html'. Please open this file in your browser to view the diagram.")

######################################################################################################

def household_installation_distribution(csv_path):
    """
    Plots the distribution of household installation sizes (PV_surf, storage_capacity, S_inv)
    as mono-dimensional scatter plots (strip plots) for each technology, ignoring bus ID.
    """
    df = pd.read_csv(csv_path)
    relevant_names = ['PV_surf', 'storage_capacity', 'S_inv']
    filtered = df[df['Name'].isin(relevant_names)]

    # Prepare data for each technology
    pv_surf = filtered[filtered['Name'] == 'PV_surf']['Value'].values * 0.2
    storage_capacity = filtered[filtered['Name'] == 'storage_capacity']['Value'].values*1000
    s_inv = filtered[filtered['Name'] == 'S_inv']['Value'].values*1000

    # Plot mono-dimensional scatter (strip) plots
    fig, axs = plt.subplots(3, 1, figsize=(8, 7), sharex=False)

    axs[0].scatter(pv_surf, [0]*len(pv_surf), alpha=0.3, color='tab:blue', s=40)
    axs[0].set_yticks([])
    axs[0].set_xlabel('PV_surf')
    axs[0].set_title('Distribution of PV_surf')

    axs[1].scatter(storage_capacity, [0]*len(storage_capacity), alpha=0.3, color='tab:orange', s=40)
    axs[1].set_yticks([])
    axs[1].set_xlabel('Storage Capacity')
    axs[1].set_title('Distribution of Storage Capacity')

    axs[2].scatter(s_inv, [0]*len(s_inv), alpha=0.3, color='tab:green', s=40)
    axs[2].set_yticks([])
    axs[2].set_xlabel('S_inv')
    axs[2].set_title('Distribution of S_inv')

    plt.tight_layout()
    plt.show()




def check_subs(csv_file_path):

    # --- Load data ---
    subs_hv_P = defaultdict(dict)
    subs_hv_Q = defaultdict(dict)
    subs_hv_capacity = defaultdict(dict)

    subs_mv_P = defaultdict(dict)
    subs_mv_Q = defaultdict(dict)
    subs_mv_capacity = defaultdict(dict)

    with open(csv_file_path, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            tag = row[0]
            if tag not in ('subs_hv_P', 'subs_hv_Q', 'subs_hv_capacity', 'subs_mv_P', 'subs_mv_Q', 'subs_mv_capacity'):
                continue
            if tag in ('subs_hv_P', 'subs_hv_Q', 'subs_mv_P', 'subs_mv_Q'):
                t = row[1]
            value = float(row[-1])

            if tag == 'subs_hv_P':
                subs = row[4]
                subs_hv_P[t][subs] = value
            elif tag == 'subs_hv_Q':
                subs = row[4]
                subs_hv_Q[t][subs] = value
            elif tag == 'subs_hv_capacity':
                subs = row[4]
                subs_hv_capacity[subs] = value
            elif tag == 'subs_mv_P':
                subs = row[5]
                subs_mv_P[t][subs] = value
            elif tag == 'subs_mv_Q':
                subs = row[5]
                subs_mv_Q[t][subs] = value
            elif tag == 'subs_mv_capacity':
                subs = row[5]
                subs_mv_capacity[subs] = value

    # --- Check constraints ---
    def check_apparent_power(S_dict, P_dict, Q_dict, label):
        print(f"\nChecking {label} substation apparent power constraints...")
        violations = 0
        for t in P_dict:
            for s in P_dict[t]:
                P = P_dict[t][s]
                Q = Q_dict[t][s]
                S = S_dict.get(s, None)
                if S is None:
                    print(f"Warning: Missing S value for {label} substation {s} at time {t}")
                    continue
                lhs = S**2
                rhs = P**2 + Q**2
                if lhs + 1e-6 < rhs:  # Tolerance for numerical precision
                    print(f"Violation at t={t}, substation={s}: S²={lhs:.4f} < P²+Q²={rhs:.4f}")
                    violations += 1
        if violations == 0:
            print("All constraints respected.")
        else:
            print(f"Total violations: {violations}")

    # Run checks
    check_apparent_power(subs_hv_capacity, subs_hv_P, subs_hv_Q, "HV")
    check_apparent_power(subs_mv_capacity, subs_mv_P, subs_mv_Q, "MV")

def check_storage(csv_file_path):

    # --- load data ---
    charging_data    = defaultdict(dict)
    discharging_data = defaultdict(dict)
    energy_data      = defaultdict(dict)
    buses_with_storage = set()

    with open(csv_file_path, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            tag = row[0]
            if tag in ('P_storage_charge','P_storage_discharge','storage_energy'):
                bus = float(row[6])
                val = float(row[-1])
                t = float(row[1])
                buses_with_storage.add(bus)
                if tag == 'P_storage_charge':
                    charging_data[bus][t] = abs(val)
                elif tag == 'P_storage_discharge':
                    discharging_data[bus][t] = val
                elif tag == 'storage_energy':
                    energy_data[bus][t] = val

    def plot_bus_activity(bus_id):
        bus = float(bus_id)
        ch  = charging_data[bus]
        dis = discharging_data[bus]
        en  = energy_data[bus]

        # 1) power vs time + max_power
        ts   = sorted(set(ch) | set(dis))
        ch_s = [ch.get(t,0) for t in ts]
        dis_s= [dis.get(t,0) for t in ts]

        plt.figure(figsize=(8,4))
        plt.plot(ts, ch_s,  '-o', label='Charge')
        plt.plot(ts, dis_s, '-o', label='Discharge')
        plt.title(f'Bus {bus} Power')
        plt.xlabel('timestep'); plt.ylabel('power')
        plt.legend(); plt.grid(True); plt.tight_layout()
        plt.show()

        # 2) ΔE vs “net” = (charge*eff - discharge/eff)*ΔT, aligned at same t1
        ets = sorted(en)
        deltaE = []
        netEff = []
        t_plot = []
        for i in range(len(ets)-1):
            t0, t1 = ets[i], ets[i+1]
            # skip free‐start‐of‐day
            if ((t1-1) % 24) == 0:
                continue
            # actual energy change from t0→t1
            dE = en[t1] - en[t0]
            # “net” injection during period t1
            net = (ch.get(t1,0)*STORAGE_EFFICIENCY - dis.get(t1,0)/STORAGE_EFFICIENCY) * DELTA_T

            deltaE.append(dE)
            netEff.append(net)
            t_plot.append(t1)

        plt.figure(figsize=(8,4))
        plt.plot(t_plot, deltaE, '-o', label='ΔEnergy actual')
        plt.plot(t_plot, netEff,'-x', label='Net = chg·η − dis/η')
        plt.title(f'Bus {bus} Energy Balance (with efficiency)')
        plt.xlabel('timestep'); plt.ylabel('energy change')
        plt.legend(); plt.grid(True); plt.tight_layout()
        plt.show()

        # 3) daily ratio: E[end] / E[start], want ≥ VAR
        days, daily_ratio = [], []
        for t in ets:
            if ((t-1) % 24) == 0:              # start‑of‑day at t
                start_t = t
                end_t   = t + 23
                if end_t in en:
                    days.append(int((t-1)//24) + 1)
                    if en[start_t] != 0:
                        daily_ratio.append((en[end_t])/( en[start_t]))
                    else:
                        daily_ratio.append((en[end_t]+ 0.0001)/( en[start_t]+ 0.0001)) # avoid div by 0

        plt.figure(figsize=(8,4))
        plt.bar(days, daily_ratio)
        plt.axhline(STORAGE_DAILY_MAX_VARIATION, color='r', linestyle='--',
                    label=f'{STORAGE_DAILY_MAX_VARIATION} threshold')
        plt.title(f'Bus {bus} Daily End/Start Energy Ratio')
        plt.xlabel('day index')
        plt.ylabel('E[end] / E[start]')
        plt.legend()
        plt.grid(True, axis='y')
        plt.tight_layout()
        plt.show()
        
    # Example

    # Only plot buses that have nonzero storage capacity/activity
    for bus in buses_with_storage:
        # Check if the bus has any nonzero charging, discharging, or energy data
        has_data = (
            any(abs(v) > 1e-8 for v in charging_data[bus].values()) or
            any(abs(v) > 1e-8 for v in discharging_data[bus].values()) or
            any(abs(v) > 1e-8 for v in energy_data[bus].values())
        )
        if has_data:
            plot_bus_activity(bus)

def check_pv(csv_path, bus = None):
    # Read the CSV file
    df = pd.read_csv(csv_path)  # Replace with your file path

    # Extract data into dictionaries
    s_sun = {}      # Dictionary for production values
    pv_surf = {}    # Dictionary for PV surface area
    irr = {}        # Dictionary for Irradiation
    s_inv = {}      # Dictionary for Maximum inverter capacity

    for _, row in df.iterrows():
        name = row['Name']
        if name == 'P_inv':
            period = float(row['periods'])
            bus = str(row['buses'])
            val = row['Value']
            s_sun[(period, bus)] = val
        elif name == 'PV_surf':
            bus = str(row['buses'])
            val = row['Value']
            pv_surf[bus] = val
        elif name == 'Irr':
            period = float(row['periods'])
            val = row['Value']
            irr[period] = val
        elif name == 'S_inv':
            bus = str(row['buses'])
            val = row['Value']
            s_inv[bus] = val

    # Filter valid buses (PV_surf > 0) and periods (Irr > 0)
    valid_buses = sorted([b for b in pv_surf if pv_surf[b] > 0], key=lambda x: float(x))
    valid_periods = sorted([p for p in irr if irr[p] > 0], key=lambda x: float(x))

    # Compute the ratio: S_sun / min(PV_surf * Irr * 0.2 / 1000, S_inv)
    data = []
    for period in valid_periods:
        for bus in valid_buses:
            actual = s_sun.get((period, bus), 0.0)
            pv = pv_surf[bus]
            i = irr[period]
            prod_irr = (pv * i * 0.2)/ BASE_POWER  # Convert to same units as S_inv (MW?)
            inv_lim = s_inv.get(bus, 0.0)
            max_prod = prod_irr
            ratio = round(actual / max_prod , 3)
            data.append({'Period': period, 'Bus': bus, 'Ratio': ratio})
    # Create a DataFrame and pivot for heatmap
    heatmap_df = pd.DataFrame(data)
    heatmap_pivot = heatmap_df.pivot(index='Period', columns='Bus', values='Ratio')

    # Plot heatmap
    plt.figure(figsize=(12, 8))
    sns.heatmap(
        heatmap_pivot,
        annot=True,
        fmt=".2f",
        cmap='viridis',
        vmin=0,         
        vmax=1.0,        
        cbar_kws={'label': 'Actual / Max Production'}
    )
    plt.title('PV Production Efficiency (S_sun / min(Irr-based, Inverter Limit))')
    plt.xlabel('Bus')
    plt.ylabel('Period')
    plt.tight_layout()
    plt.show()

    if bus is not None:
        bus_surf = pv_surf[f"{bus}"]
        production = []
        max_production = []
        for period in valid_periods:
            actual = s_sun[(period, f"{bus}")]
            max = irr[period]
            max_production.append((bus_surf * max * 0.2)/ BASE_POWER)
            production.append(actual)
        plt.plot(valid_periods, production, label='Actual Production')
        plt.plot(valid_periods, max_production, label='Max Production')
        plt.title(f'Bus {bus} - Actual vs Max Production')
        plt.xlabel('Period')
        plt.ylabel('Production (MW)')
        plt.legend()
        plt.show()

def power_check(csv_file_path):
    
    # --- load data ---
    pv_data    = defaultdict(dict)
    load_data = defaultdict(dict)
    import_data      = defaultdict(dict)
    losses_data      = defaultdict(dict)

    with open(csv_file_path, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            tag = row[0]
            if tag in ('P_load','P_sun','subs_hv_P', 'losses'):
                val = float(row[-1])
                t = float(row[1])
                if tag == 'P_load':
                    bus = float(row[6])
                    load_data[bus][t] = val
                elif tag == 'P_sun':
                    bus = float(row[6])
                    pv_data[bus][t] = val
                elif tag == 'subs_hv_P':
                    bus = float(row[4])
                    import_data[bus][t] = val
                elif tag == 'losses':
                    bus = float(row[2])
                    losses_data[bus][t] = val


    total_load = sum(sum(values.values()) for values in load_data.values())
    total_pv = sum(sum(values.values()) for values in pv_data.values())
    total_import = sum(sum(values.values()) for values in import_data.values())
    total_losses = sum(sum(values.values()) for values in losses_data.values())
    net = total_load - total_pv - total_import + total_losses

    print(f"Total Load: {total_load}")
    print(f"Total PV: {total_pv}")
    print(f"Total Import: {total_import}")
    print(f"Total Losses: {total_losses}")

    print(f"Net: {net}")

def bus_check(csv_path: str, bus_ids: list):
    """
    Reads the CSV of optimal values, aggregates active power data for the given bus ids,
    and plots the load profile including:
    - Base Load (P_load, multiplied by -1)
    - PV Production (P_sun, as positive)
    - Battery Injection (computed as P_storage_discharge + (-P_storage_charge))
    - Net Load (P_bus)
    
    The aggregation groups data by the 'periods' column, summing the values
    for the specified bus IDs.
    
    Parameters:
    csv_path (str): Path to the CSV file (optimal_values.csv)
    bus_ids (list): List of bus IDs (as they appear in the 'buses' column)
    """
    
    # Read the CSV file
    df = pd.read_csv(csv_path)
    
    # Ensure the bus IDs are numeric and filter the rows by bus_ids
    df['buses'] = pd.to_numeric(df['buses'], errors='coerce')
    df_filtered = df[df['buses'].isin(bus_ids)]
    
    # Pivot the DataFrame: rows are 'periods', columns are variable names in 'Name', values from 'Value' and aggregated by sum.
    pivot = df_filtered.pivot_table(index='periods', columns='Name', values='Value', aggfunc='sum')
    
    # Retrieve data for each variable. If missing, default to zero.
    # Base Load: multiply by -1 so that load appears as negative.
    base_load = -pivot.get('P_load', pd.Series(0, index=pivot.index))
    
    # PV Production: keep positive.
    pv_production = pivot.get('P_sun', pd.Series(0, index=pivot.index))
    
    # Battery Charge: multiply by -1 to make charging negative.
    battery_charge = -pivot.get('P_storage_charge', pd.Series(0, index=pivot.index))
    
    # Battery Discharge: remains positive.
    battery_discharge = pivot.get('P_storage_discharge', pd.Series(0, index=pivot.index))
    
    # Battery Injection: combine discharge and modified charge.
    battery_injection = battery_discharge + battery_charge  # equivalent to: discharge - original charge
    
    # Net Load: as provided.
    net_load = pivot.get('P_bus', pd.Series(0, index=pivot.index))
    
    # Plotting active power profiles.
    plt.figure(figsize=(10, 6))
    
    plt.plot(pivot.index, base_load, label='Base Load (-P_load)', marker='o')
    plt.plot(pivot.index, pv_production, label='PV Production (P_sun)', marker='o')
    plt.plot(pivot.index, battery_injection, label='Battery Injection (P_storage_discharge + (-P_storage_charge))', marker='o')
    plt.plot(pivot.index, -net_load, label='Net Load (P_bus)', marker='o')
    
    plt.xlabel('Period')
    plt.ylabel('Active Power')
    plt.title('Aggregated Bus Load Profile')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def check_all(csv_path: str):
    """
    Run all checks on the given CSV file.
    
    Parameters:
    csv_path (str): Path to the CSV file (optimal_values.csv)
    """
    cost_check(csv_path)
    check_subs(csv_path)
    check_storage(csv_path)
    check_pv(csv_path)
    power_check(csv_path)
    bus_check(csv_path, [0.0, 1.0, 2.0])

import argparse
import pandas as pd
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run checks on a CSV file.")
    parser.add_argument("csv_path", type=str, help="Path to the CSV file (e.g., optimal_values.csv)")
    args = parser.parse_args()

    check_all(args.csv_path)

