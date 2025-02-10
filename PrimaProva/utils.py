from param import*
def plot_opt(m):
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
    
    # Extend the bounds a little
    x_max = x_max + 1
    y_max = y_max + 1
    x_min = x_min - 1
    y_min = y_min - 1

    import matplotlib.pyplot as plt

    plt.figure(figsize=(10, 10))
    plt.xlim(x_min, x_max)
    plt.ylim(y_min, y_max)

    # Plot LBUS
    for bus in m.B:
        if bus in m.buses:
            x = LBUS[bus].x_coord
            y = LBUS[bus].y_coord
            plt.scatter(LBUS[bus].x_coord, LBUS[bus].y_coord, s=100, c='blue', marker='o', label='LBUS' if bus == list(LBUS.keys())[0] else "")
        elif bus in m.subs:
            x = SUBS[bus].x_coord
            y = SUBS[bus].y_coord
            plt.scatter(SUBS[bus].x_coord, SUBS[bus].y_coord, s=100, c='red', marker='s', label='SUBS' if bus == list(SUBS.keys())[0] else "")

        bus_voltage = sum(m.voltage_squared[p,bus].value**0.5 for p in m.periods)/len(m.periods)
        plt.text(
            x-0.15,  # x-coordinate of the bus
            y+0.15,  # y-coordinate of the bus
            f'{bus_voltage:.2f}',  # Voltage value formatted to 2 decimal places
            fontsize=10,           # Font size
            color='black',         # Text color
            bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3'),  # Styled box
            horizontalalignment='center',  # Center text horizontally
            verticalalignment='bottom'     # Place text above the point
        )

    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    import numpy as np

    # Suppose line_ids is a list of all unique line_id values extracted from LINES
    unique_conductors = sorted({LINES_OPT[conductor].code_word for conductor in LINES_OPT})
    num_condunductors = len(unique_conductors)
    colormap = cm.get_cmap('tab10', num_condunductors)  # 'tab10' has 10 distinct colors; choose another if needed
    # Create a mapping from line_id to a color (converted to a hex or RGBA)
    color_mapping = {code_word: colormap(i) for i, code_word in enumerate(unique_conductors)}

    # Add a legend for the code words and their corresponding colors
    for code_word, color in color_mapping.items():
        plt.plot([], [], color=color, label=code_word)
    plt.legend(title='Code Words')

    # Plot lines based on the activated lines and conductors
    for line in m.lines:
        print(f"Checking line {line}")
        if m.line_act[line].value == 1:  # If line is activated
            print(f"Line {line} is activated.")
            
            # Get from_bus and to_bus based on whether they are LBUS or SUBS
            from_bus = LINES[line].from_bus
            to_bus = LINES[line].to_bus

            # Check if the bus is from LBUS or SUBS and retrieve the correct coordinates
            if from_bus in LBUS:
                from_bus_coords = (LBUS[from_bus].x_coord, LBUS[from_bus].y_coord)
            elif from_bus in SUBS:
                from_bus_coords = (SUBS[from_bus].x_coord, SUBS[from_bus].y_coord)

            if to_bus in LBUS:
                to_bus_coords = (LBUS[to_bus].x_coord, LBUS[to_bus].y_coord)
            elif to_bus in SUBS:
                to_bus_coords = (SUBS[to_bus].x_coord, SUBS[to_bus].y_coord)

            # Plot the line with the conductor selected
            for conductor in m.conductors:
                print(f"Conductor {conductor} activation status: {m.line_opt[line,conductor].value}")
                if m.line_opt[line, conductor].value == 1:  # If this conductor is selected
                    print(f"  Conductor {conductor} is used for this line.")
                    # Get the color corresponding to the line's conductor
                    color = color_mapping.get(conductor, 'black')  # defaults to 'black' if line_id not found
                    plt.plot([from_bus_coords[0], to_bus_coords[0]],
                            [from_bus_coords[1], to_bus_coords[1]],
                            linestyle='-', color=color, linewidth=3)
                    
                    # Calculate the midpoint of the line
                    midpoint_x = (from_bus_coords[0] + to_bus_coords[0]) / 2
                    midpoint_y = (from_bus_coords[1] + to_bus_coords[1]) / 2

                    # Retrieve current, active and reactive power for the considered line
                    current = max(m.current_squared[p, line].value for p in m.periods)**0.5
                    active_power = sum(m.active_power[p, line].value for p in m.periods) / len(m.periods)
                    reactive_power = sum(m.reactive_power[p, line].value for p in m.periods) / len(m.periods)

                    # Display the current, active and reactive power at the midpoint of the line
                    plt.text(
                        midpoint_x + 0.15,  # x-coordinate of the text
                        midpoint_y - 0.15,  # y-coordinate of the text
                        f'I: {current:.2f} A\nP: {active_power:.2f} MW\nQ: {reactive_power:.2f} MVar',  # Formatted text
                        fontsize=8,          # Font size
                        color='black',       # Text color
                        bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3'),  # Styled box
                        horizontalalignment='center',  # Center text horizontally
                        verticalalignment='top'        # Place text below the point
                    )
                    
                            

        else:
            print(f"Line {line} is not activated.")
            # If the line is not activated, plot it as a dashed line
            from_bus = LINES[line].from_bus
            to_bus = LINES[line].to_bus

            # Get coordinates for from_bus and to_bus, check their types
            if from_bus in LBUS:
                from_bus_coords = (LBUS[from_bus].x_coord, LBUS[from_bus].y_coord)
            elif from_bus in SUBS:
                from_bus_coords = (SUBS[from_bus].x_coord, SUBS[from_bus].y_coord)

            if to_bus in LBUS:
                to_bus_coords = (LBUS[to_bus].x_coord, LBUS[to_bus].y_coord)
            elif to_bus in SUBS:
                to_bus_coords = (SUBS[to_bus].x_coord, SUBS[to_bus].y_coord)

            # Plot the line with dashed style if not activated
            plt.plot([from_bus_coords[0], to_bus_coords[0]],
                     [from_bus_coords[1], to_bus_coords[1]],
                     linestyle=':', color='black')

    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.title('Bus Locations')
    plt.legend()
    plt.grid(True)
    plt.show()
