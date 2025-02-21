from import_file import load_conductors_csv, load_bus, load_lines_csv
from import_file import load_Mycampus
from generate_lines_v1 import generate_lines
from terza_prova import optimize

N_PERIODS_MAX = 1

file_path = 'conductors.csv'
LINES_OPT = load_conductors_csv(file_path)

folder_path = r"C:\Users\mogli\OneDrive\Desktop\Tesi\Campus data\UpdatedData"

cities = ["Buenos Aires", "Los Angeles", "Singapore", "Vancouver"]  #For this cities the opt is infeasible
cities = ["Miami", "Guayaquil"]     #Weird result both on objective value and topology
cities = ["Abu Dhabi", "Brussels", "Copenhagen", "Montreal", "Tucson"] #This seem to work fine
cities = ["Abu Dhabi"]

for city in cities:
    LBUS, SUBS, SLACK, updated_buildings  = load_bus(folder_path, city, N_PERIODS_MAX)
    
    keyes = list(LBUS.keys())
    N_PERIODS = len(LBUS[keyes[1]].load_kW)

    generate_lines(LBUS|SUBS|SLACK)
    print("Lines generated and saved to lines.csv successfully!")
    LINES = load_lines_csv(LBUS|SUBS|SLACK)

    from test_plot import*
    test(LBUS|SUBS|SLACK,LINES)
    plot_opt(LBUS, SUBS, SLACK, LINES, LINES_OPT, N_PERIODS)
    #exit()
    
    
    optimize(LBUS, SUBS, SLACK, LINES, LINES_OPT, N_PERIODS)

