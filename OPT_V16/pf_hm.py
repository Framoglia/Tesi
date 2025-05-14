import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from validation import export_and_solve
from debug import plot_comparisons, debug_pandapower_net
import dill

def pf_hm(results, pp_bus_map, pp_line_map):
    voltage_df = pd.DataFrame()
    loading_df = pd.DataFrame()

    inv_bus_map = {v: k for k, v in pp_bus_map.items()}
    inv_line_map = {v: k for k, v in pp_line_map.items()}


    for t, res in results.items():
        # Bus voltages
        if res["bus"] is not None:
            bus_series = res["bus"]["vm_pu"].copy()
            bus_series.index = bus_series.index.map(inv_bus_map)  # Map to original IDs
            voltage_df[t] = bus_series

        # Line loadings
        if res["line"] is not None:
            line_series = res["line"]["loading_percent"].copy()
            line_series.index = line_series.index.map(inv_line_map)  # Map to original IDs
            loading_df[t] = line_series

    # Transpose: rows = time, columns = original IDs
    voltage_df = voltage_df.T
    loading_df = loading_df.T

    plt.figure(figsize=(12, 6))
    sns.heatmap(voltage_df, cmap="viridis", cbar_kws={'label': 'Voltage (p.u.)'})
    plt.title("Bus Voltages Over Time")
    plt.xlabel("Original Bus ID")
    plt.ylabel("Time Step")
    plt.tight_layout()
    plt.savefig("bus_voltages.png")
    plt.close()

    # Line Loading Heatmap
    plt.figure(figsize=(12, 6))
    sns.heatmap(loading_df, cmap="magma", cbar_kws={'label': 'Line Loading (%)'})
    plt.title("Line Loadings Over Time")
    plt.xlabel("Original Line ID")
    plt.ylabel("Time Step")
    plt.tight_layout()
    plt.savefig("line_loadings.png")
    plt.close()


with open("model.pkl", "rb") as f:
    loaded_data = dill.load(f)

# Extract the individual variables from the loaded dictionary
model = loaded_data["model"]
LBUS = loaded_data["LBUS"]
SUBS = loaded_data["SUBS"]
SLACK = loaded_data["SLACK"]
LINES = loaded_data["LINES"]
LINES_OPT = loaded_data["LINES_OPT"]
N_PERIODS = loaded_data["N_PERIODS"]
if "irradiation" in loaded_data:
    irradiation = loaded_data["irradiation"]


net, pp_bus_map, pp_line_map, results = export_and_solve(model, LBUS, SUBS, SLACK, LINES, LINES_OPT)
pf_hm(results, pp_bus_map, pp_line_map)
pf_vs_opt = plot_comparisons(net, results, model, pp_bus_map)

exit()

# Get the internal pandapower line index for original line ID 40
original_line_id = 40
pp_idx = pp_line_map[original_line_id]

# Extract current in kA over time for this line
line_current = {}

for t, res in results.items():
    if res["line"] is not None and pp_idx in res["line"].index:
        line_current[t] = res["line"].loc[pp_idx, "i_ka"]

# Convert to a pandas Series
current_series = pd.Series(line_current).sort_index()

# Plot
plt.figure(figsize=(10, 4))
plt.plot(current_series.index, current_series.values, marker='o', linestyle='-')
plt.title(f"Line Current Over Time (Line ID {original_line_id})")
plt.xlabel("Time Step")
plt.ylabel("Current (kA)")
plt.grid(True)
plt.tight_layout()
plt.savefig(f"line_current_{original_line_id}.png")
plt.close()

