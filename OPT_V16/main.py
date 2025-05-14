from import_file import *
from optimization import *
from validation import *
from debug import *
from representative_days import *
import dill
from optimization_zero import *

# LOAD DATA--------------------------------------

cities = ["Mycampus", "Abu Dhabi", "Brussels", "Buenos Aires", "Copenhagen", "Los Angeles", "Singapore", "Vancouver", "Montreal", "Tucson", "Miami", "Guayaquil"]
cities = "Mycampus"

#Read data from file
LINES_OPT = load_conductors_csv()
LBUS, SUBS, SLACK, irradiation = load_bus(cities)
EV_option = False
mv_load_counts = load_ev(LBUS, EV_option)

LINES = get_top_n_topologies(SUBS, LBUS, SLACK, 1)
#LINES = get_topologies_by_substation(SUBS, LBUS, SLACK)
'''plot_topology_basic(LBUS, SUBS, SLACK, LINES)'''

#Create stages data
stages = [0,1,2]
LBUS_list = update_bus_loads(LBUS, stages)

#Select representative days from last stage
write_csv(LBUS_list[stages[-1]], irradiation, "aggregate demand.csv")
run_daysxtractor()

#Extract representative days data
representative_LBUS_list = []
for stage in stages:
    new_LBUS, new_irradiation, weights = extract_representative_days(LBUS_list[stage], irradiation, "days.csv")
    representative_LBUS_list.append(new_LBUS)


keyes = list(representative_LBUS_list[0].keys())
N_PERIODS = len(representative_LBUS_list[0][keyes[1]].load_kW)

initial_config = {}
folders_created = []

for stage in stages:
    folder_name= f"from_terminal_{stage}"
    model, logg = optimize_log(representative_LBUS_list[stage], SUBS, SLACK, LINES, LINES_OPT, N_PERIODS, new_irradiation, EV_option, weights, initial_config, stage) #Do i warm start this with lines?
    initial_config = model

    data = {
        "model": model,
        "LBUS": representative_LBUS_list[stage],
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

    fig = plot_network_solution_2(model, representative_LBUS_list[stage], SUBS, SLACK, LINES, LINES_OPT)

    net, pp_bus_map, pp_line_map, results = export_and_solve(model, representative_LBUS_list[stage], SUBS, SLACK, LINES, LINES_OPT)
    pf_hm(results, pp_bus_map, pp_line_map)
    pf_vs_opt = plot_comparisons(net, results, model, pp_bus_map)
    debug_pandapower_net(net)
    #easy_plot(net)

    new_folder = move_files_to_folder(folder_name)
    folders_created.append(new_folder)

group_folders(folders_created, group_name='all_stages_from_terminal')



