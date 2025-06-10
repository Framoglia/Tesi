from import_file_graph import *
from optimization import * 
from validation import *
from debug import *
from representative_days import *
from checks import *

# LOAD DATA--------------------------------------


cities = ["Newcampus", "Mycampus", "Abu Dhabi", "Brussels", "Buenos Aires", "Copenhagen", "Los Angeles", "Singapore", "Vancouver", "Montreal", "Tucson", "Miami", "Guayaquil"]
cities = "Montreal"  # For testing purposes, you can change this to any city in the list

#Read data from file
LINES_OPT = load_conductors_csv(BASE_DIR / "Campus data" / "MyCampus" / "conductors.csv")
LBUS, SUBS, SLACK, irradiation = load_bus(cities)

write_csv(LBUS, irradiation, "aggregate demand.csv")
run_daysxtractor()


folders = []
district_results = {}
index = 0
iterations = {}

for district in set(b.district for b in LBUS.values() if b.district and b.district != 'TFO'):

    LBUS_d = {bus_id: bus for bus_id, bus in LBUS.items() if bus.district == district}
    SUBS_d = {bus_id: bus for bus_id, bus in SUBS.items() if bus.district == district}
            
    LINES, index = load_lines(LBUS_d | SUBS_d | SLACK, index)
    plot_topology_basic(LBUS_d, SUBS_d, SLACK, LINES)

    new_LBUS_d, new_irradiation, weights = extract_representative_days(LBUS_d, irradiation, "days.csv")

    N_PERIODS = len(new_LBUS_d[list(new_LBUS_d.keys())[1]].load_kW)
    initial_config = {}
    folder_name= f"{district}"
    iterations[district] = {}
    count = 0
    black_list = []
    enne = 5
    cond_table, ranked_conductors = build_cond_table(LINES, LINES_OPT)

    

    while True:
        if count > 0:
            old_cond_table = copy.deepcopy(cond_table)
            loading_data = loading_data_from_model(solved_model, new_LBUS_d|SUBS_d|SLACK, LINES, LINES_OPT, cond_table, ranked_conductors)
            for k,v in loading_data.items():
                print(f"Line {k}, loading: {v:.2f}")
            upgradable_lines = {k:v for k,v in loading_data.items() if solved_model.line_opt[k,ranked_conductors[-1]].value < 0.8}
            upgradable_lines = {k:v for k,v in upgradable_lines.items() if k not in black_list}
            for k,v in LINES.items():
                print(f"line {k} worst conductors  opt -> {solved_model.line_opt[k,ranked_conductors[-1]].value}")
            if not upgradable_lines:
                print("No more upgradable lines. Stopping.")
                break
            
            sorted_items = sorted(upgradable_lines.items(), key=lambda x: x[1])[:enne]
            line_ids = [item[0] for item in sorted_items]
            enne = min(enne, len(line_ids))

            downgrade_conductors(cond_table, ranked_conductors, line_ids)

            iterations[district][count] = line_ids

        try:
            model, logg = optimize_log(new_LBUS_d, SUBS_d, SLACK, LINES, LINES_OPT, N_PERIODS, new_irradiation, weights, initial_config, cond_table)

            s = float(model.C_PV.value) * 2
            solved_model= copy.deepcopy(model)
            valid_cond_tables = copy.deepcopy(cond_table) 
            print(f"Iteration {count}, model solved successfully.")
            
        except TypeError:
            if count == 0:
                print("TypeError on first iteration, skipping district.")
                break
            if enne != 1:
                print(f"Iteration {count}, downgrade failed. Reverting.")
                cond_table = copy.deepcopy(old_cond_table)
            
                enne -= 1
            else:
                print(f"Iteration {count}, downgrade failed and n == 1. Stopping.")
                copy.deepcopy(cond_table)
                black_list.append(line_ids[0])
                print(f"Blacklisted line {line_ids[0]}.")
                print(black_list)

        if count == 0:  # first time you trim unused lines
            LINES = {line_id: line for line_id, line in LINES.items() if model.line_act[line_id].value >= 0.8}
            cond_table = {key: value for key, value in cond_table.items() if model.line_act[key].value >= 0.8}


        count += 1


    fig = plot_network_solution_2(solved_model, new_LBUS_d, SUBS_d, SLACK, LINES, LINES_OPT)
    export_optimal_values(solved_model)
    net, pp_bus_map, pp_line_map, results = export_and_solve(solved_model, new_LBUS_d, SUBS_d, SLACK, LINES, LINES_OPT)
    voltage_df, loading_df = pf_hm(results, pp_bus_map, pp_line_map)
    pf_vs_opt = plot_comparisons(net, results, solved_model, pp_bus_map)
    plot_opt(solved_model, new_LBUS_d, SUBS_d, SLACK, LINES, LINES_OPT, N_PERIODS)

    if count != 0:
        
        district_results[district] = {
            "model": solved_model,
            "LBUS": new_LBUS_d,
            "SUBS": SUBS_d,
            "LINES": LINES,
            "irradiation": new_irradiation,  
            "cond_table": valid_cond_tables      
        }
    
    for k, v in iterations[district].items():
        print(f"{k}: {(v)}")
    new_folder = move_files_to_folder(folder_name)
    folders.append(new_folder)


merge_district_results(folders, 'final_optimal_values.csv')
plot_opt_district(district_results, SLACK, LINES_OPT)
cost_check("final_optimal_values.csv")
sankey_cost_check("final_optimal_values.csv")
group_folders(folders, group_name=cities)





