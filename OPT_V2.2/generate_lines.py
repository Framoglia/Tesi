import csv

def generate_lines(updated_buildings):
    # Extract substations (buildings without active_power)
    subs = [b for b in updated_buildings.values() if not b.active_power]
    districts = {}

    for b in updated_buildings.values():
        if b.active_power:
            district = b.district
            if district not in districts:
                districts[district] = []
            districts[district].append(b)
    
    lines = []
    line_id = 0

    # Connect each substation with the first building in each district
    for sub in subs:
        for district, buildings in districts.items():
            if buildings:
                lines.append((line_id, sub.building_id, buildings[0].building_id))
                line_id += 1
    
    # Connect every substation to each other
    for i in range(len(subs)):
        for j in range(i + 1, len(subs)):
            lines.append((line_id, subs[i].building_id, subs[j].building_id))
            line_id += 1
    
    # Connect buildings within the same district
    for district, buildings in districts.items():
        for i in range(len(buildings)):
            for j in range(i + 1, len(buildings)):
                lines.append((line_id, buildings[i].building_id, buildings[j].building_id))
                line_id += 1
    
    # Write lines to a CSV file with Line ID
    with open('lines.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Line ID', 'from bus', 'to bus'])  # Header
        for line in lines:
            writer.writerow(line)

