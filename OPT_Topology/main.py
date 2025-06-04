from import_file_graph import *
from optimization_topology import *
from debug import *
from representative_days import *

# LOAD DATA--------------------------------------

cities = ["Newcampus", "Mycampus", "Abu Dhabi", "Brussels", "Buenos Aires", "Copenhagen", "Los Angeles", "Singapore", "Vancouver", "Montreal", "Tucson", "Miami", "Guayaquil"]
cities = "Vancouver"

#Read data from file
LINES_OPT = load_conductors_csv(BASE_DIR / "Campus data" / "MyCampus" / "conductors.csv")
LBUS, SUBS, SLACK, irradiation = load_bus(cities)
count = 0
while True:
    index = 0
    for district in set(b.district for b in LBUS.values() if b.district and b.district != 'TFO'):

        LBUS_d = {bus_id: bus for bus_id, bus in LBUS.items() if bus.district == district}
        SUBS_d = {bus_id: bus for bus_id, bus in SUBS.items() if bus.district == district}
                
        LINES, index = load_lines(LBUS_d | SUBS_d | SLACK, index)
        plot_topology_basic(LBUS_d, SUBS_d, SLACK, LINES)

        #Select representative days from last stage
        write_csv(LBUS_d, irradiation, "aggregate demand.csv")
        run_daysxtractor()
        new_LBUS_d, new_irradiation, weights = extract_representative_days(LBUS_d, irradiation, "days.csv")

        N_PERIODS = len(new_LBUS_d[list(new_LBUS_d.keys())[1]].load_kW)
        
        model, logg = optimize_log(new_LBUS_d, SUBS_d, SLACK, LINES, LINES_OPT, N_PERIODS)
        
        name = f"{district}_{count}"
        export_optimal_values(model, name)
        try:
            plot_opt(model, new_LBUS_d, SUBS_d, SLACK, LINES, LINES_OPT, N_PERIODS, name)
        except :
            print(f"{district} in iteration {count} is infeasible")
            exit()


        bus_ids = list(LBUS_d.keys()) + list(SUBS_d.keys()) + list(SLACK.keys())
        selected_lines = {line_id: line for line_id, line in LINES.items() if model.line_act[line_id].value >= 0.5}

        is_radial = is_radial_topology(bus_ids, selected_lines, debug= False)
        if is_radial == False:
            print(f"Topology is not radial for district {district} in iteration {count}.")
            exit()
        
    
    count += 1