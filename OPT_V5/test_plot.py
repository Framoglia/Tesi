import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm


def test(BUS, LINES):
    number_slack = 0
    number_sub = 0
    number_lv_load = 0
    number_mv_load = 0

    for bus in BUS:
        if BUS[bus].b_type == 'HV_sub':
            number_slack += 1
        elif BUS[bus].b_type == 'MV_sub':
            number_sub += 1
        elif BUS[bus].b_type == 'LV_load':
            print(BUS[bus].load_kW)
            number_lv_load += 1
        elif BUS[bus].b_type == 'MV_load':
            print(BUS[bus].load_kW)
            number_mv_load += 1

    print("\nSystem Summary:")
    print("=========================")
    print(f"High Voltage Substations : {number_slack}")
    print(f"Medium Voltage Substations: {number_sub}")
    print(f"Low Voltage Loads        : {number_lv_load}")
    print(f"Medium Voltage Loads     : {number_mv_load}")
    print("=========================\n")

def plot_opt(LBUS, SUBS, SLACK, LINES, LINES_OPT, N_PERIODS):
    x_max = 0
    y_max = 0
    x_min = 99
    y_min = 99

    # Get the max and min coordinates from both LBUS and SUBS
    for BUS in LBUS:
        x_max = max(x_max, LBUS[BUS].x_coord)
        y_max = max(y_max, LBUS[BUS].y_coord)
        x_min = min(x_min, LBUS[BUS].x_coord)
        y_min = min(y_min, LBUS[BUS].y_coord)

    for BUS in SUBS:
        x_max = max(x_max, SUBS[BUS].x_coord)
        y_max = max(y_max, SUBS[BUS].y_coord)
        x_min = min(x_min, SUBS[BUS].x_coord)
        y_min = min(y_min, SUBS[BUS].y_coord)

    for BUS in SLACK:
        x_max = max(x_max, SLACK[BUS].x_coord)
        y_max = max(y_max, SLACK[BUS].y_coord)
        x_min = min(x_min, SLACK[BUS].x_coord)
        y_min = min(y_min, SLACK[BUS].y_coord)
    
    
    # Extend the bounds a little
    x_max = x_max + 10
    y_max = y_max + 10
    x_min = x_min - 10
    y_min = y_min - 10

    import matplotlib.pyplot as plt

    plt.figure(figsize=(10, 10))
    plt.xlim(x_min, x_max)
    plt.ylim(y_min, y_max)

    # Plot LBUS
    type_markers = {
        "HV_sub": ("s", "red"),   # Square, Red
        "MV_sub": ("D", "orange"), # Diamond, Orange
        "LV_sub": ("^", "yellow"), # Triangle, Yellow
        "MV_load": ("o", "green"), # Circle, Green
        "LV_load": ("x", "blue")   # X, Blue
    }

    for bus in LBUS | SUBS | SLACK:
        if bus in LBUS:
            x = LBUS[bus].x_coord
            y = LBUS[bus].y_coord
            b_type = LBUS[bus].b_type  # Assuming each bus has a 'p_type' attribute
        elif bus in SLACK:
            x = SLACK[bus].x_coord
            y = SLACK[bus].y_coord
            b_type = SLACK[bus].b_type  # Assuming each substation has a 'p_type' attribute
        else:
            x = SUBS[bus].x_coord
            y = SUBS[bus].y_coord
            b_type = SUBS[bus].b_type
            
        
        marker, color = type_markers.get(b_type, ("o", "black"))  # Default to black circle if unknown
        plt.scatter(x, y, s=100, c=color, marker=marker, label=b_type)

    # Plot lines based on the activated lines and conductors
    for line in LINES:
        from_bus = LINES[line].from_bus
        to_bus = LINES[line].to_bus

        # Check if the bus is from LBUS or SUBS and retrieve the correct coordinates
        if from_bus in LBUS:
            from_bus_coords = (LBUS[from_bus].x_coord, LBUS[from_bus].y_coord)
        elif from_bus in SUBS:
            from_bus_coords = (SUBS[from_bus].x_coord, SUBS[from_bus].y_coord)
        else:
            from_bus_coords = (SLACK[from_bus].x_coord, SLACK[from_bus].y_coord)

        if to_bus in LBUS:
            to_bus_coords = (LBUS[to_bus].x_coord, LBUS[to_bus].y_coord)
        elif to_bus in SUBS:
            to_bus_coords = (SUBS[to_bus].x_coord, SUBS[to_bus].y_coord)
        else:
            to_bus_coords = (SLACK[to_bus].x_coord, SLACK[to_bus].y_coord)

        # Plot the line with dashed style if not activated
        plt.plot([from_bus_coords[0], to_bus_coords[0]],
                    [from_bus_coords[1], to_bus_coords[1]],
                    linestyle=':', color='black')
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.title('Bus Locations')
    plt.grid(True)
    plt.show()