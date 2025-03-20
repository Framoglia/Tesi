from import_file import load_conductors_csv, load_bus, load_lines
from optimization import *
from validation import *
from debug import *
import dill

cities = ["Buenos Aires", "Los Angeles", "Singapore", "Vancouver"]      #For this cities the opt is infeasible
cities = ["Miami", "Guayaquil"]                                         #Weird result both on objective value and topology
cities = ["Abu Dhabi", "Brussels", "Copenhagen", "Montreal", "Tucson"]  #This seem to work fine
cities = "Copenhagen"

START_DATE = (6,7,5)  #Day, Month, Hour
N_PERIODS_MAX = 12

LINES_OPT = load_conductors_csv()
LBUS, SUBS, SLACK, irradiation = load_bus(cities, N_PERIODS_MAX, START_DATE)
LINES = load_lines(SUBS | LBUS | SLACK)

#test_plot(LBUS, SUBS, SLACK, LINES)

keyes = list(LBUS.keys())
N_PERIODS = len(LBUS[keyes[1]].load_kW)

folder_name= "Copenhagen_half_day"

model, logg = optimize_log(LBUS, SUBS, SLACK, LINES, LINES_OPT, N_PERIODS, irradiation) 

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

fig = plot_network_solution(model, LBUS, SUBS, SLACK, LINES, LINES_OPT)

net, pp_bus_map, results = export_and_solve(model, LBUS, SUBS, SLACK, LINES, LINES_OPT)

debug_pandapower_net(net)
#easy_plot(net)

pf_vs_opt = plot_comparisons(net, results, model, pp_bus_map)
move_files_to_folder(folder_name)
    



