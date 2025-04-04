from import_file import load_conductors_csv, load_bus, load_lines
from optimization import *
from validation import *
from debug import *
from representative_days import *
import dill

cities = ["Mycampus", "Abu Dhabi", "Brussels", "Buenos Aires", "Copenhagen", "Los Angeles", "Singapore", "Vancouver", "Montreal", "Tucson", "Miami", "Guayaquil"]
cities = "Mycampus"

LINES_OPT = load_conductors_csv()
LBUS, SUBS, SLACK, irradiation = load_bus(cities)
#print(SUBS)
LINES = load_lines(SUBS | LBUS | SLACK)

write_csv(LBUS, irradiation, "aggregate demand.csv")
run_daysxtractor()
new_LBUS, new_irradiation, weights = extract_representative_days(LBUS, irradiation, "days.csv")
#test_plot(LBUS, SUBS, SLACK, LINES)

keyes = list(new_LBUS.keys())
N_PERIODS = len(new_LBUS[keyes[1]].load_kW)

folder_name= "My_campus_w_initial_sub_3_active"

model, logg = optimize_log(LBUS, SUBS, SLACK, LINES, LINES_OPT, N_PERIODS, irradiation, weights) 

data = {
    "model": model,
    "LBUS": LBUS,
    "SUBS": SUBS,
    "SLACK": SLACK,
    "LINES": LINES,
    "LINES_OPT": LINES_OPT,
    "N_PERIODS": N_PERIODS,
    "irradiation": irradiation        
}

with open("model.pkl", "wb") as f:
    dill.dump(data, f)

export_optimal_values(model)

fig = plot_network_solution_2(model, LBUS, SUBS, SLACK, LINES, LINES_OPT)

net, pp_bus_map, results = export_and_solve(model, LBUS, SUBS, SLACK, LINES, LINES_OPT)
#debug_pandapower_net(net)
#easy_plot(net)
#pf_vs_opt = plot_comparisons(net, results, model, pp_bus_map)

move_files_to_folder(folder_name)
    



