import csv
import math

def calculate_distance(bus1, bus2):
    """Euclidean distance between two buses."""
    return math.sqrt((bus1.x_coord - bus2.x_coord)**2 + (bus1.y_coord - bus2.y_coord)**2)

def get_cell_centroid(cell, min_x, min_y, grid_width, grid_height):
    """Return the center (x,y) of the given cell (grid_x, grid_y)."""
    grid_x, grid_y = cell
    center_x = min_x + (grid_x + 0.5) * grid_width
    center_y = min_y + (grid_y + 0.5) * grid_height
    return (center_x, center_y)

def get_extreme_node(loads, direction, centroid):
    """
    Given a list of nodes (loads) and a direction (tuple, e.g. (-1,-1)), return the node
    with the highest projection onto the normalized direction vector, measured from centroid.
    (A higher projection means the node is more in that direction.)
    """
    dx, dy = direction
    norm = math.sqrt(dx*dx + dy*dy)
    if norm == 0:
        return None
    ux, uy = dx / norm, dy / norm
    best = None
    best_proj = -float('inf')
    for load in loads:
        # Compute vector from centroid to node.
        vx = load.x_coord - centroid[0]
        vy = load.y_coord - centroid[1]
        proj = vx * ux + vy * uy
        if proj > best_proj:
            best_proj = proj
            best = load
    return best

def find_neighbor_cell_in_quadrant(grid_x, grid_y, quadrant, grid_cells, max_search_distance):
    """
    Search outward along the exact line defined by quadrant (a tuple, e.g. (-1,-1)) from cell (grid_x, grid_y)
    and return the coordinates of the first cell (within max_search_distance) that exists in grid_cells.
    Returns None if none is found.
    """
    for d in range(1, max_search_distance + 1):
        candidate = (grid_x + d * quadrant[0], grid_y + d * quadrant[1])
        if candidate in grid_cells and grid_cells[candidate]:
            return candidate
    return None

def get_closest_nodes_in_quadrants(buses, target_bus):
    """
    For a given target bus, find the closest buses in each of the four quadrants:
    NE (North-East), NW (North-West), SE (South-East), SW (South-West)
    """
    closest_buses = {'NE': None, 'NW': None, 'SE': None, 'SW': None}
    closest_distances = {'NE': float('inf'), 'NW': float('inf'), 'SE': float('inf'), 'SW': float('inf')}
    
    for bus in buses:
        if bus == target_bus:
            continue
        
        # Determine the quadrant of the bus from the target bus
        dx = bus.x_coord - target_bus.x_coord
        dy = bus.y_coord - target_bus.y_coord
        
        if dx >= 0 and dy > 0:  # North-East (NE)
            quadrant = 'NE'
        elif dx < 0 and dy >= 0:  # North-West (NW)
            quadrant = 'NW'
        elif dx > 0 and dy <= 0:  # South-East (SE)
            quadrant = 'SE'
        elif dx <= 0 and dy < 0:  # South-West (SW)
            quadrant = 'SW'
        else:
            continue  # The node is directly on one of the axes, so we skip it for quadrants
        
        # Calculate the distance from target bus to this bus
        distance = calculate_distance(target_bus, bus)
        
        # Update the closest bus in the corresponding quadrant
        if distance < closest_distances[quadrant]:
            closest_buses[quadrant] = bus
            closest_distances[quadrant] = distance
    
    return closest_buses

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

    lines_set = set()

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
        for mv_load in mv_loads:
            # Find the closest MV_load in each quadrant
            closest_mvs = get_closest_nodes_in_quadrants(mv_loads, mv_load)

            # Add the connections to lines (if valid)
            for quadrant in ['NE', 'NW', 'SE', 'SW']:
                closest_mv = closest_mvs[quadrant]
                if closest_mv:                    
                    line = tuple(sorted([mv_load.bus_id, closest_mv.bus_id]))
                    if line not in lines_set:
                        lines.append((line_id, mv_load.bus_id, closest_mv.bus_id))
                        lines_set.add(line)
                        line_id += 1

    # 6. Connect every LV_load to every other LV_load in the same district
    for district, types in buses_by_district.items():
        lv_loads = types['LV_load']
        
        if len(lv_loads) == 0:
            continue

        grid_size = 10
        max_search_distance= grid_size
    
    # Determine border coordinates.
        min_x = min(load.x_coord for load in lv_loads)
        max_x = max(load.x_coord for load in lv_loads)
        min_y = min(load.y_coord for load in lv_loads)
        max_y = max(load.y_coord for load in lv_loads)

        grid_width = (max_x - min_x) / grid_size
        grid_height = (max_y - min_y) / grid_size

        # Build dictionary: cell (grid_x, grid_y) -> list of loads.
        grid_cells = {}
        for load in lv_loads:
            grid_x = int((load.x_coord - min_x) // grid_width)
            grid_y = int((load.y_coord - min_y) // grid_height)
            cell = (grid_x, grid_y)
            grid_cells.setdefault(cell, []).append(load)

        def connect_buses(bus1, bus2):
            nonlocal line_id
            if bus1.bus_id == bus2.bus_id:
                return
            line = tuple(sorted([bus1.bus_id, bus2.bus_id]))
            if line not in lines_set:
                lines.append((line_id, bus1.bus_id, bus2.bus_id))
                lines_set.add(line)
                line_id += 1

        # --- Intra-cell connections ---
        for cell, loads in grid_cells.items():
            for i in range(len(loads)):
                for j in range(i + 1, len(loads)):
                    connect_buses(loads[i], loads[j])

        # --- Row/Column neighbor connections ---
        def connect_along_direction(cell, dx, dy):
            grid_x, grid_y = cell
            # Start from the immediate neighbor cell and go outward.
            x = grid_x + dx
            y = grid_y + dy
            while 0 <= x < grid_size and 0 <= y < grid_size:
                if (x, y) in grid_cells and grid_cells[(x, y)]:
                    # Use a representative node from the current cell and connect to all nodes in the found neighbor.
                    for neighbor_load in grid_cells[(x, y)]:
                        connect_buses(grid_cells[cell][0], neighbor_load)
                    break
                x += dx
                y += dy

        for cell in grid_cells:
            for (dx, dy) in [(-1,0), (1,0), (0,-1), (0,1)]:
                connect_along_direction(cell, dx, dy)

        # --- Quadrant connections using the "extreme node" criterion ---
        # For each cell, for each diagonal quadrant:
        quadrant_directions = [(-1,-1), (1,-1), (-1,1), (1,1)]
        for cell, loads in grid_cells.items():
            grid_x, grid_y = cell
            # Compute cell centroid.
            centroid = get_cell_centroid(cell, min_x, min_y, grid_width, grid_height)
            # From current cell, select the node most in the quadrant direction.
            for quad in quadrant_directions:
                best_current = get_extreme_node(loads, quad, centroid)
                if best_current is None:
                    continue
                # Search for neighbor cell in that quadrant.
                neighbor_cell = find_neighbor_cell_in_quadrant(grid_x, grid_y, quad, grid_cells, max_search_distance)
                if neighbor_cell is None:
                    continue
                neighbor_centroid = get_cell_centroid(neighbor_cell, min_x, min_y, grid_width, grid_height)
                # From the neighbor cell, choose the node that is most "toward" the current cell,
                # i.e. extreme in the opposite direction.
                opposite = (-quad[0], -quad[1])
                best_neighbor = get_extreme_node(grid_cells[neighbor_cell], opposite, neighbor_centroid)
                if best_neighbor is not None:
                    connect_buses(best_current, best_neighbor)

    # Write lines to a CSV file with Line ID
    with open('lines.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Line ID', 'from bus', 'to bus'])  # Header
        for line in lines:
            writer.writerow(line)

