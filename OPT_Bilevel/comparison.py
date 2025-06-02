from debug import *
import dill
from validation import *

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
if loaded_data.get("irradiation") is not None:
    irradiation = loaded_data["irradiation"]

net, pp_bus_map, pp_line_map, results = export_and_solve(model, LBUS, SUBS, SLACK, LINES, LINES_OPT)
pf_vs_opt = plot_comparisons(net, results, model, pp_bus_map)
