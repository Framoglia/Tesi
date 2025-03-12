from import_file import load_conductors_csv, load_bus, load_lines
from linearization_test import load_setting, move_files_to_folder
from optimization import *
from validation import *
from debug import *

cities = ["Buenos Aires", "Los Angeles", "Singapore", "Vancouver"]      #For this cities the opt is infeasible
cities = ["Miami", "Guayaquil"]                                         #Weird result both on objective value and topology
cities = ["Abu Dhabi", "Brussels", "Copenhagen", "Montreal", "Tucson"]  #This seem to work fine
cities = "Mycampus"

N_PERIODS_MAX = 12

LINES_OPT = load_conductors_csv()
LBUS, SUBS, SLACK, irradiation = load_bus(cities, N_PERIODS_MAX)
print(irradiation)

LINES = load_lines(SUBS | LBUS | SLACK)
#test_plot(LBUS, SUBS, SLACK, LINES)

keyes = list(LBUS.keys())
N_PERIODS = len(LBUS[keyes[1]].load_kW)

setting_list, folder_name = load_setting()

settings = {}
for i, setting in setting_list.items():

    model, logg = optimize_log(LBUS, SUBS, SLACK, LINES, LINES_OPT, N_PERIODS, setting, irradiation)  

    export_optimal_values(model, setting)

    net, pp_bus_map, results = export_and_solve(model, LBUS, SUBS, SLACK, LINES, LINES_OPT)

    debug_pandapower_net(net)
    #custom_load_plot(net)         TODO: Implement this
    #easy_plot(net, setting)

    pf_vs_opt = plot_comparisons(net, results, model, pp_bus_map, setting)
    settings[tuple(setting)] = pf_vs_opt, logg

table_result_2(settings, folder_name)

move_files_to_folder(folder_name)
    



