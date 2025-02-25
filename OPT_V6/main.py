from import_file import load_conductors_csv, load_bus, load_lines_csv
from import_file import load_Mycampus
from generate_lines_v1 import generate_lines
from terza_prova_p_neg import optimize
from validation import *
from print_opt import export_optimal_values
from utils import plot_opt
from compare_voltages import plot_voltage_comparison

N_PERIODS_MAX = 1

file_path = 'conductors.csv'
LINES_OPT = load_conductors_csv(file_path)

folder_path = r"C:\Users\mogli\OneDrive\Desktop\Tesi\Campus data\UpdatedData"

cities = ["Buenos Aires", "Los Angeles", "Singapore", "Vancouver"]  #For this cities the opt is infeasible
cities = ["Miami", "Guayaquil"]     #Weird result both on objective value and topology
cities = ["Abu Dhabi", "Brussels", "Copenhagen", "Montreal", "Tucson"] #This seem to work fine
cities = "Mycampus"

if cities != "Mycampus":
    for city in cities:
        LBUS, SUBS, updated_buildings  = load_bus(folder_path, city, N_PERIODS_MAX)

        keyes = list(LBUS.keys())
        N_PERIODS = len(LBUS[keyes[1]].load_kW)

        generate_lines(updated_buildings)
        print("Lines generated and saved to lines.csv successfully!")
        LINES = load_lines_csv(SUBS,LBUS)

        optimize(LBUS, SUBS, LINES, LINES_OPT, N_PERIODS)

else:
    LBUS, SUBS, SLACK = load_Mycampus(N_PERIODS_MAX)
    keyes = list(LBUS.keys())
    N_PERIODS = len(LBUS[keyes[1]].load_kW)

    generate_lines(SUBS | LBUS | SLACK)
    print("Lines generated and saved to lines.csv successfully!")
    LINES = load_lines_csv(SUBS | LBUS | SLACK)
    
    model = optimize(LBUS, SUBS, SLACK, LINES, LINES_OPT, N_PERIODS)


plot_opt(model, LBUS, SUBS, SLACK, LINES, LINES_OPT, N_PERIODS)
export_optimal_values(model)
net, pp_bus_map = export_and_solve(model, LBUS, SUBS, SLACK, LINES, LINES_OPT)
debug_pandapower_net(net)

plot_voltage_comparison(net, model, pp_bus_map)

