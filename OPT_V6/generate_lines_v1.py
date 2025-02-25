import csv

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
            buses_by_district[b.district] = {'MV_sub': [], 'LV_sub': [], 'MV_load': [], 'LV_load': []}
        
        if b.b_type == 'MV_sub':
            buses_by_district[b.district]['MV_sub'].append(b)
        elif b.b_type == 'LV_sub':
            buses_by_district[b.district]['LV_sub'].append(b)
        elif b.b_type == 'MV_load':
            buses_by_district[b.district]['MV_load'].append(b)
        elif b.b_type == 'LV_load':
            buses_by_district[b.district]['LV_load'].append(b)
    
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
        mv_subs = types['MV_sub']
        mv_loads = types['MV_load']
        
        for mv_sub in mv_subs:
            for mv_load in mv_loads:
                lines.append((line_id, mv_sub.substation_id, mv_load.bus_id))
                line_id += 1
    
    """# 3. Connect every LV_sub to every MV_sub in the same district
    for district, types in buses_by_district.items():
        lv_subs = types['LV_sub']
        mv_subs = types['MV_sub']
        
        for lv_sub in lv_subs:
            for mv_sub in mv_subs:
                lines.append((line_id, lv_sub.substation_id, mv_sub.substation_id))
                line_id += 1
    
    # 4. Connect every LV_sub to every LV_load in the same district
    for district, types in buses_by_district.items():
        lv_subs = types['LV_sub']
        lv_loads = types['LV_load']
        
        for lv_sub in lv_subs:
            for lv_load in lv_loads:
                lines.append((line_id, lv_sub.substation_id, lv_load.bus_id))
                line_id += 1"""
    

    import math

    lines_temp = set()


    # New. Connect every MV_subs to every LV_load in the same district
    for district, types in buses_by_district.items():
        mv_subs = types['MV_sub']
        lv_loads = types['LV_load']
        
        for mv_sub in mv_subs:
            for lv_load in lv_loads:
                lines.append((line_id, mv_sub.substation_id, lv_load.bus_id))
                line_id += 1

    # 5. Connect every MV_load to every other MV_load in the same district
    for district, types in buses_by_district.items():
        mv_loads = types['MV_load']
        
        for bus in mv_loads:  # Loop through each bus
            distances = []

            for other_bus in mv_loads:
                if bus.bus_id != other_bus.bus_id:  # Avoid self-connections
                    distance = math.sqrt((bus.x_coord - other_bus.x_coord) ** 2 + (bus.y_coord - other_bus.y_coord) ** 2)
                    distances.append((distance, tuple(sorted([bus.bus_id, other_bus.bus_id]))))

            # Sort by distance and pick the 3 closest
            distances.sort()
            for _, connection in distances[:3]:
                lines_temp.add(connection)  # Add to the set (ensuring no duplicates)

    # Step 2: Convert to list and assign line_id
    sorted_lines = sorted(lines_temp)  # Sort connections again
    for bus1, bus2 in sorted_lines:
        lines.append((line_id, bus2, bus1))
        line_id += 1


    """# 6. Connect every LV_load to every other LV_load in the same district
    for district, types in buses_by_district.items():
        lv_loads = types['LV_load']
        
        for i in range(len(lv_loads)):
            for j in range(i + 1, len(lv_loads)):  # Avoid duplicate connections
                lines.append((line_id, lv_loads[i].bus_id, lv_loads[j].bus_id))
                line_id += 1"""

    
    # Use a set to avoid duplicate connections
    lines_temp_lv = set()


    # Step 1: Find the 3 closest buses for each bus
    for district, types in buses_by_district.items():
        lv_loads = types['LV_load']

        for bus in lv_loads:  # Loop through each bus
            distances = []

            for other_bus in lv_loads:
                if bus.bus_id != other_bus.bus_id:  # Avoid self-connections
                    distance = math.sqrt((bus.x_coord - other_bus.x_coord) ** 2 + (bus.y_coord - other_bus.y_coord) ** 2)
                    distances.append((distance, tuple(sorted([bus.bus_id, other_bus.bus_id]))))

            # Sort by distance and pick the 3 closest
            distances.sort()
            for _, connection in distances[:3]:
                lines_temp_lv.add(connection)  # Add to the set (ensuring no duplicates)

    # Step 2: Convert to list and assign line_id
    sorted_lines = sorted(lines_temp)  # Sort connections again
    for bus1, bus2 in sorted_lines:
        lines.append((line_id, bus2, bus1))
        line_id += 1

    # Write lines to a CSV file with Line ID
    with open('lines.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Line ID', 'from bus', 'to bus'])  # Header
        for line in lines:
            writer.writerow(line)