from import_file_graph import *
from optimization import * 
from validation import *
from debug import *
from representative_days import *

# LOAD DATA--------------------------------------
print("1")
cities = ["Newcampus", "Mycampus", "Abu Dhabi", "Brussels", "Buenos Aires", "Copenhagen", "Los Angeles", "Singapore", "Vancouver", "Montreal", "Tucson", "Miami", "Guayaquil"]
cities = "Brussels"
print("2")
#Read data from file
LINES_OPT = load_conductors_csv(BASE_DIR / "Campus data" / "MyCampus" / "conductors.csv")
LBUS, SUBS, SLACK, irradiation = load_bus(cities)
print("3")
folders = []
district_results = {}
index = 0
print("4")
for district in set(b.district for b in LBUS.values() if b.district and b.district != 'TFO'):
    print("5")
    LBUS_d = {bus_id: bus for bus_id, bus in LBUS.items() if bus.district == district}
    SUBS_d = {bus_id: bus for bus_id, bus in SUBS.items() if bus.district == district}
            
    LINES, index = load_lines(LBUS_d | SUBS_d | SLACK, index)
    plot_topology_basic(LBUS_d, SUBS_d, SLACK, LINES)
    print("6")
    #Select representative days from last stage
    write_csv(LBUS_d, irradiation, "aggregate demand.csv")
    run_daysxtractor()
    new_LBUS_d, new_irradiation, weights = extract_representative_days(LBUS_d, irradiation, "days.csv")

    N_PERIODS = len(new_LBUS_d[list(new_LBUS_d.keys())[1]].load_kW)
    initial_config = {}
    folder_name= f"{district}"
    count = 0
    models= []
    print("7")
    cond_table, ranked_conductors = build_cond_table(LINES, LINES_OPT)

    while True:   
        if count != 0:
            upgradable_loading_df = get_lines_with_upgradable_conductors(cond_table, ranked_conductors, loading_df)
            lowest_max_columns = upgradable_loading_df.max().nsmallest(3).index.tolist()
            #threshold = 40
            #lowest_max_columns = upgradable_loading_df.max()[upgradable_loading_df.max() < threshold].index.tolist()
            if not lowest_max_columns:
                break
            cond_table = downgrade_conductors(cond_table, ranked_conductors, lowest_max_columns)
        print("8")
        model, logg = optimize_log(new_LBUS_d, SUBS_d, SLACK, LINES, LINES_OPT, N_PERIODS, new_irradiation, weights, initial_config, cond_table)
        models.append(model)
        try:
            fig = plot_network_solution_2(models[-2], new_LBUS_d, SUBS_d, SLACK, LINES, LINES_OPT, count)
            plot_opt(model, new_LBUS_d, SUBS_d, SLACK, LINES, LINES_OPT, N_PERIODS)
            export_optimal_values(model, count)
            net, pp_bus_map, pp_line_map, results = export_and_solve(model, new_LBUS_d, SUBS_d, SLACK, LINES, LINES_OPT)
            voltage_df , loading_df = pf_hm(results, pp_bus_map, pp_line_map, count)
        except TypeError:
            break  
        print("9")
        #save_pkl(model, new_LBUS_d, SUBS_d, SLACK, LINES, LINES_OPT, N_PERIODS, irradiation)
        pf_vs_opt = plot_comparisons(net, results, model, pp_bus_map)
        #debug_pandapower_net(net)
        #easy_plot(net)
        
        if count == 0:
            LINES = {line_id: line for line_id, line in LINES.items() if model.line_act[line_id].value >= 0.8}
            cond_table = {key: value for key, value in cond_table.items() if model.line_act[key].value >= 0.8}
        
        count += 1
    
    pf_vs_opt = plot_comparisons(net, results, models[-2], pp_bus_map)
    district_results[district] = {
        "model": models[-2],
        "LBUS": new_LBUS_d,
        "SUBS": SUBS_d,
        "LINES": LINES,
        "irradiation": new_irradiation,  
        "cond_table": cond_table      
    }

    new_folder = move_files_to_folder(folder_name)
    folders.append(new_folder)

plot_opt_district(district_results, SLACK, LINES_OPT)
group_folders(folders, group_name='Abu Dhabi')





