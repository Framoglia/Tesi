from import_file import load_conductors_csv, load_bus, load_lines_csv
from import_file import load_Mycampus
from generate_lines import generate_lines
from terza_prova import optimize

N_PERIODS_MAX = 2

file_path = 'conductors_perf.csv'
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
        N_PERIODS = len(LBUS[keyes[1]].load_MW)

        generate_lines(updated_buildings)
        print("Lines generated and saved to lines.csv successfully!")
        LINES = load_lines_csv(SUBS,LBUS)

        optimize(LBUS, SUBS, LINES, LINES_OPT, N_PERIODS)

else:
    LBUS, SUBS = load_Mycampus(N_PERIODS_MAX)

    keyes = list(LBUS.keys())
    N_PERIODS = len(LBUS[keyes[1]].load_MW)

    generate_lines(SUBS | LBUS)
    print("Lines generated and saved to lines.csv successfully!")
    LINES = load_lines_csv(SUBS,LBUS)

    optimize(LBUS, SUBS, LINES, LINES_OPT, N_PERIODS)

