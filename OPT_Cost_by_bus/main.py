from import_file_graph import *
from optimization_c_elec import *
from validation import *
from debug import *
from representative_days import *
import dill
from optimization_zero import *

# LOAD DATA--------------------------------------

cities = ["Newcampus", "Mycampus", "Abu Dhabi", "Brussels", "Buenos Aires", "Copenhagen", "Los Angeles", "Singapore", "Vancouver", "Montreal", "Tucson", "Miami", "Guayaquil"]
cities = "Brussels"

#Read data from file
LINES_OPT = load_conductors_csv()
LBUS, SUBS, SLACK, irradiation = load_bus(cities)

"""LBUS = {bus_id: bus for bus_id, bus in LBUS.items() if bus.district == "Marolles"}  # Remove slack bus from LBUS
SUBS = {bus_id: bus for bus_id, bus in SUBS.items() if bus.district == "Marolles"}  # Remove slack bus from LBUS"""


LINES = load_lines(LBUS | SUBS | SLACK)
plot_topology_basic(LBUS, SUBS, SLACK, LINES)


#Select representative days from last stage
write_csv(LBUS, irradiation, "aggregate demand.csv")
run_daysxtractor()


new_LBUS, new_irradiation, weights = extract_representative_days(LBUS, irradiation, "days.csv")


N_PERIODS = len(new_LBUS[list(new_LBUS.keys())[1]].load_kW)

initial_config = {}

folder_name= f"Brusels_27_05"
model, logg = optimize_log(new_LBUS, SUBS, SLACK, LINES, LINES_OPT, N_PERIODS, new_irradiation, weights, initial_config)
#initial_config = model

data = {
    "model": model,
    "LBUS": new_LBUS,
    "SUBS": SUBS,
    "SLACK": SLACK,
    "LINES": LINES,
    "LINES_OPT": LINES_OPT,
    "N_PERIODS": N_PERIODS,
    "irradiation": new_irradiation        
}

with open("model.pkl", "wb") as f:
    dill.dump(data, f)

export_optimal_values(model)

fig = plot_network_solution_2(model, new_LBUS, SUBS, SLACK, LINES, LINES_OPT)

net, pp_bus_map, pp_line_map, results = export_and_solve(model, new_LBUS, SUBS, SLACK, LINES, LINES_OPT)
pf_hm(results, pp_bus_map, pp_line_map)
#pf_vs_opt = plot_comparisons(net, results, model, pp_bus_map)
#debug_pandapower_net(net)
#easy_plot(net)

new_folder = move_files_to_folder(folder_name)



