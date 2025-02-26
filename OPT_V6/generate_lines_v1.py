import csv
import math

def generate_lines(BUS):
    # Extract substations and loads
    hv_subs = [b for b in BUS.values() if b.b_type == 'HV_sub']
    mv_subs = [b for b in BUS.values() if b.b_type == 'MV_sub']
    lv_subs = [b for b in BUS.values() if b.b_type == 'LV_sub']
    mv_loads = [b for b in BUS.values() if b.b_type == 'MV_load']
    lv_loads = [b for b in BUS.values() if b.b_type == 'LV_load']

    # Group buses by district for MV_sub, LV_sub, and loads
    buses_by_district = {}

    for b in BUS.values():
        if b.district not in buses_by_district:
            buses_by_district[b.district] = {
                'HV_sub': [],  # Added to prevent KeyError
                'MV_sub': [],
                'LV_sub': [],
                'MV_load': [],
                'LV_load': []
            }
        
        buses_by_district[b.district][b.b_type].append(b)
    
    # Prepare lines list
    lines = []
    line_id = 0

    # 1. Connect every HV_sub to every MV_sub (independent of district)
    for hv_sub in hv_subs:
        for mv_sub in mv_subs:
            lines.append((line_id, hv_sub.substation_id, mv_sub.substation_id))
            line_id += 1
    
    # 2. Connect every MV_sub to every MV_load in the same district
    for district, types in buses_by_district.items():
        mv_subs_district = types['MV_sub']
        mv_loads_district = types['MV_load']  # Use only district-specific loads
        
        for mv_sub in mv_subs_district:
            for mv_load in mv_loads_district:
                lines.append((line_id, mv_sub.substation_id, mv_load.bus_id))
                line_id += 1

    lines_temp = set()

    # 3. Connect every MV_sub to every LV_load in the same district
    for district, types in buses_by_district.items():
        mv_subs_district = types['MV_sub']
        lv_loads_district = types['LV_load']
        
        for mv_sub in mv_subs_district:
            for lv_load in lv_loads_district:
                lines.append((line_id, mv_sub.substation_id, lv_load.bus_id))
                line_id += 1

    # 4. Connect every MV_load to every other MV_load in the same district
    for district, types in buses_by_district.items():
        mv_loads_district = types['MV_load']
        
        for bus in mv_loads_district:
            distances = []

            for other_bus in mv_loads_district:
                if bus.bus_id != other_bus.bus_id:
                    distance = math.sqrt((bus.x_coord - other_bus.x_coord) ** 2 + (bus.y_coord - other_bus.y_coord) ** 2)
                    distances.append((distance, tuple(sorted([bus.bus_id, other_bus.bus_id]))))

            # Sort by distance and pick the 3 closest
            distances.sort()
            for _, connection in distances[:3]:
                lines_temp.add(connection)

    # Assign line IDs to MV_load connections
    sorted_lines = sorted(lines_temp)
    for bus1, bus2 in sorted_lines:
        lines.append((line_id, bus2, bus1))
        line_id += 1

    # Use a set to avoid duplicate LV_load connections
    lines_temp_lv = set()

    # 5. Connect every LV_load to every other LV_load in the same district
    for district, types in buses_by_district.items():
        lv_loads_district = types['LV_load']

        for bus in lv_loads_district:
            distances = []

            for other_bus in lv_loads_district:
                if bus.bus_id != other_bus.bus_id:
                    distance = math.sqrt((bus.x_coord - other_bus.x_coord) ** 2 + (bus.y_coord - other_bus.y_coord) ** 2)
                    distances.append((distance, tuple(sorted([bus.bus_id, other_bus.bus_id]))))

            # Sort by distance and pick the 3 closest
            distances.sort()
            for _, connection in distances[:3]:
                lines_temp_lv.add(connection)

    # Assign line IDs to LV_load connections
    sorted_lines_lv = sorted(lines_temp_lv)
    for bus1, bus2 in sorted_lines_lv:
        lines.append((line_id, bus2, bus1))
        line_id += 1

    # 6. Connect every MV_sub to every other MV_sub in the same district (NEW)
    lines_temp_mv_sub = set()

    for district, types in buses_by_district.items():
        mv_subs_district = types['MV_sub']

        for mv1 in mv_subs_district:
            for mv2 in mv_subs_district:
                if mv1.substation_id != mv2.substation_id:
                    connection = tuple(sorted([mv1.substation_id, mv2.substation_id]))
                    lines_temp_mv_sub.add(connection)  # Avoid duplicate (A, B) == (B, A)

    sorted_lines_mv_sub = sorted(lines_temp_mv_sub)
    for bus1, bus2 in sorted_lines_mv_sub:
        lines.append((line_id, bus2, bus1))
        line_id += 1

    # Write lines to CSV
    with open('lines.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Line ID', 'from bus', 'to bus'])
        for line in lines:
            writer.writerow(line)
