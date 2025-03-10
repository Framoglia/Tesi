from import_file import load_conductors_csv, load_bus, load_lines
from linearization_test import linearization_possibilities
from optimization import *
from validation import *
from debug import *

cities = ["Buenos Aires", "Los Angeles", "Singapore", "Vancouver"]      #For this cities the opt is infeasible
cities = ["Miami", "Guayaquil"]                                         #Weird result both on objective value and topology
cities = ["Abu Dhabi", "Brussels", "Copenhagen", "Montreal", "Tucson"]  #This seem to work fine
cities = "Brussels"

N_PERIODS_MAX = 1

LINES_OPT = load_conductors_csv()
LBUS, SUBS, SLACK = load_bus(cities, N_PERIODS_MAX)
LINES = load_lines(SUBS | LBUS | SLACK)
#test_plot(LBUS, SUBS, SLACK, LINES)

keyes = list(LBUS.keys())
N_PERIODS = len(LBUS[keyes[1]].load_kW)

lin_poss = linearization_possibilities()

esperiments = {}
for i, lin in lin_poss.items():
    model = optimize_log(LBUS, SUBS, SLACK, LINES, LINES_OPT, N_PERIODS, lin)  

    export_optimal_values(model, lin)

    net, pp_bus_map, results = export_and_solve(model, LBUS, SUBS, SLACK, LINES, LINES_OPT)
    #debug_pandapower_net(net)
    #custom_load_plot(net)         TODO: Implement this
    easy_plot(net, lin)
    esperiment = plot_comparisons(net, results, model, pp_bus_map, lin)
    print(precision(esperiment))




    

    



