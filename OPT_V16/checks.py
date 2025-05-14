import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import csv
from collections import defaultdict
from param import *
import seaborn as sns
from utils import BASE_POWER

def cost_check():
    # Load data
    df = pd.read_csv('optimal_values.csv')
    df = df.set_index('Name')
    # --- CAPEX components ---
    capex_items = {
        'Conductor': df.loc['C_cond', 'Value'],
        'hv Substation': df.loc['C_subs_hv', 'Value'] + df.loc['subs_hv_inst_cost', 'Value'],
        'mv Substation': df.loc['C_subs_mv', 'Value'] + df.loc['subs_mv_inst_cost', 'Value'],
        'PV': df.loc['C_PV', 'Value'] + df.loc['C_inv', 'Value'] + df.loc['PV_inst_cost', 'Value'],
        'Storage': df.loc['C_storage_capacity', 'Value'] + df.loc['C_storage_power', 'Value'] + df.loc['storage_inst_cost', 'Value'],
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
        df.loc['C_storage_power', 'Value'],
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

def check_subs():

    # Path to the CSV file
    csv_file_path = 'optimal_values.csv'

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
            value = float(row[10])

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

def check_storage():
    csv_file_path = 'optimal_values.csv'

    # --- load data ---
    charging_data    = defaultdict(dict)
    discharging_data = defaultdict(dict)
    energy_data      = defaultdict(dict)
    storage_power    = {}
    buses_with_storage = set()

    with open(csv_file_path, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            tag = row[0]
            if tag in ('P_storage_charge','P_storage_discharge','storage_energy','storage_power'):
                bus = float(row[6])
                val = float(row[10])
                if tag == 'storage_power' and val > 0:
                    buses_with_storage.add(bus)
                    storage_power[bus] = val
                elif tag != 'storage_power':
                    t = float(row[1])
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
        max_p = storage_power.get(bus)

        # 1) power vs time + max_power
        ts   = sorted(set(ch) | set(dis))
        ch_s = [ch.get(t,0) for t in ts]
        dis_s= [dis.get(t,0) for t in ts]

        plt.figure(figsize=(8,4))
        plt.plot(ts, ch_s,  '-o', label='Charge')
        plt.plot(ts, dis_s, '-o', label='Discharge')
        if max_p is not None:
            plt.axhline(max_p, linestyle='--', label='Max Power')
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

    for bus in buses_with_storage:
        plot_bus_activity(bus)

def check_pv(bus = None):
    # Read the CSV file
    df = pd.read_csv('optimal_values.csv')  # Replace with your file path

    # Extract data into dictionaries
    s_sun = {}      # Dictionary for production values
    pv_surf = {}    # Dictionary for PV surface area
    irr = {}        # Dictionary for Irradiation
    s_inv = {}      # Dictionary for Maximum inverter capacity

    for _, row in df.iterrows():
        name = row['Name']
        if name == 'S_sun':
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
            max_prod = min(inv_lim, prod_irr)
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
        vmin=0.9,         
        vmax=1.0,        
        cbar_kws={'label': 'Actual / Max Production'}
    )
    plt.title('PV Production Efficiency (S_sun / min(Irr-based, Inverter Limit))')
    plt.xlabel('Bus')
    plt.ylabel('Period')
    plt.tight_layout()
    plt.show()

    if bus is not None:
        bus_surf = pv_surf[f"{bus}.0"]
        production = []
        max_production = []
        for period in valid_periods:
            actual = s_sun[(period, f"{bus}.0")]
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

def power_check():
    

    csv_file_path = 'optimal_values.csv'

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
                val = float(row[10])
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

