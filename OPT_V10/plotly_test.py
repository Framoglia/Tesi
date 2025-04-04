from import_file import load_conductors_csv, load_bus, load_lines
from optimization import *
from validation import *
from debug import *
import dill

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
irradiation = loaded_data["irradiation"]


fig = plot_network_solution_2(model, LBUS, SUBS, SLACK, LINES, LINES_OPT)