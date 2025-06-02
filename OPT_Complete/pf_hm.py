import argparse
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
        if res["bus"] is not None:
            bus_series = res["bus"]["vm_pu"].copy()

            # Map index from internal IDs to original IDs
            mapped_index = bus_series.index.map(inv_bus_map)

            # Keep only entries where mapping succeeded (i.e., mapped index is not NaN)
            valid_mask = ~mapped_index.isnull()
            bus_series = bus_series[valid_mask]
            bus_series.index = mapped_index[valid_mask]

            # Add to the voltage DataFrame only if something is left
            if not bus_series.empty:
                voltage_df[t] = bus_series


        if res["line"] is not None:
            line_series = res["line"]["loading_percent"].copy()
            line_series.index = line_series.index.map(inv_line_map)
            loading_df[t] = line_series

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

    plt.figure(figsize=(12, 6))
    sns.heatmap(loading_df, cmap="magma", cbar_kws={'label': 'Line Loading (%)'})
    plt.title("Line Loadings Over Time")
    plt.xlabel("Original Line ID")
    plt.ylabel("Time Step")
    plt.tight_layout()
    plt.savefig("line_loadings.png")
    plt.close()

def main(pkl_path):
    with open(pkl_path, "rb") as f:
        loaded_data = dill.load(f)

    model = loaded_data["model"]
    LBUS = loaded_data["LBUS"]
    SUBS = loaded_data["SUBS"]
    SLACK = loaded_data["SLACK"]
    LINES = loaded_data["LINES"]
    LINES_OPT = loaded_data["LINES_OPT"]
    N_PERIODS = loaded_data["N_PERIODS"]
    irradiation = loaded_data.get("irradiation")

    net, pp_bus_map, pp_line_map, results = export_and_solve(
        model, LBUS, SUBS, SLACK, LINES, LINES_OPT
    )

    pf_hm(results, pp_bus_map, pp_line_map)
    #pf_vs_opt = plot_comparisons(net, results, model, pp_bus_map)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run power flow analysis with a .pkl model file")
    parser.add_argument("pkl_path", type=str, help="Path to the .pkl file")
    args = parser.parse_args()

    main(args.pkl_path)
