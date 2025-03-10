import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

def plot_opt(m, LBUS, SUBS, SLACK, LINES, LINES_OPT, N_PERIODS, setting):
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

    for bus in m.B | m.subs_hv:
        if bus in m.buses:
            x = LBUS[bus].x_coord
            y = LBUS[bus].y_coord
            b_type = LBUS[bus].b_type  # Assuming each bus has a 'p_type' attribute
        elif bus in m.subs_hv:
            x = SLACK[bus].x_coord
            y = SLACK[bus].y_coord
            b_type = SLACK[bus].b_type  # Assuming each substation has a 'p_type' attribute
        else:
            x = SUBS[bus].x_coord
            y = SUBS[bus].y_coord
            b_type = SUBS[bus].b_type
            
        
        marker, color = type_markers.get(b_type, ("o", "black"))  # Default to black circle if unknown
        plt.scatter(x, y, s=100, c=color, marker=marker, label=b_type if bus == list(m.B)[0] else "")
        
        bus_voltage = sum(m.voltage_squared[p,bus].value**0.5 for p in m.periods)/len(m.periods)
        """plt.text(
        x-0.15,  # x-coordinate of the bus
        y+0.15,  # y-coordinate of the bus
        f'{bus_voltage:.4f}',  # Voltage value formatted to 2 decimal places
        fontsize=10,           # Font size
        color='black',         # Text color
        bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3'),  # Styled box
        horizontalalignment='center',  # Center text horizontally
        verticalalignment='bottom'     # Place text above the point
        )"""



    # Assuming 'LINES_OPT' is already defined, and it contains the necessary information for each conductor
    # Sort the conductors by 'imax' values
    conductors = sorted(LINES_OPT, key=lambda conductor: LINES_OPT[conductor].imax_kA)

    

    # Create a monochromatic colormap based on the number of unique conductors
    num_conductors = len(conductors)
    colormap = cm.get_cmap('Blues', num_conductors)  # 'Blues' colormap
    colormap = colormap(np.linspace(0.3, 1, num_conductors))  # Start at 0.3 to avoid the very light colors

    # Create a mapping from code_word to color
    color_mapping = {code_word: colormap[i] for i, code_word in enumerate(conductors)}

    # Add a legend for the code words and their corresponding colors
    for code_word, color in color_mapping.items():
        plt.plot([], [], color=color, label=code_word)

    plt.legend()


    # Plot lines based on the activated lines and conductors
    for line in m.lines:
        ##DEBUG   print(f"Checking line {line}")
        if m.line_act_plus[line].value >= 0.8 or m.line_act_minus[line].value >= 0.8:  # If line is activated
            ##DEBUG   print(f"Line {line} is activated.")
            
            # Get from_bus and to_bus based on whether they are LBUS or SUBS
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

            # Plot the line with the conductor selected
            for conductor in m.conductors:
                ##DEBUG    print(f"Conductor {conductor} activation status: {m.line_opt[line,conductor].value}")
                if m.line_opt[line, conductor].value >= 0.8:  # If this conductor is selected
                    ##DEBUG     print(f"  Conductor {conductor} is used for this line.")
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
                    """plt.text(
                        midpoint_x + 0.15,  # x-coordinate of the text
                        midpoint_y - 0.15,  # y-coordinate of the text
                        f'I: {current:.2f} A\nP: {active_power:.2f} MW\nQ: {reactive_power:.2f} MVar',  # Formatted text
                        fontsize=8,          # Font size
                        color='black',       # Text color
                        bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3'),  # Styled box
                        horizontalalignment='center',  # Center text horizontally
                        verticalalignment='top'        # Place text below the point
                    )"""
                    
                            

        else:
            ##DEBUG   print(f"Line {line} is not activated.")
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
            """plt.plot([from_bus_coords[0], to_bus_coords[0]],
                     [from_bus_coords[1], to_bus_coords[1]],
                     linestyle=':', color='black')
            """
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.title('Bus Locations')
    plt.legend()
    plt.grid(True)
    a, b, c, d = setting
    name=f"optimal_topology_{a}_{b}_{c}_{d}.png"
    plt.savefig(name)



BASE_POWER = 1000000 #VA

BASE_VOLTAGE_HV = 70000 #V
BASE_VOLTAGE_MV = 15000 #V
BASE_VOLTAGE_LV = 400 #V

BASE_Z_HV = BASE_VOLTAGE_HV**2/BASE_POWER #Ohm  4.9e6   4.9e3
BASE_Z_MV = BASE_VOLTAGE_MV**2/BASE_POWER #Ohm  225e3   225
BASE_Z_LV = BASE_VOLTAGE_LV**2/BASE_POWER #Ohm  160     0.16

BASE_I_HV = BASE_POWER/BASE_VOLTAGE_HV #Amps    0.0143  14.3
BASE_I_MV = BASE_POWER/BASE_VOLTAGE_MV #Amps    0.0667  66.7
BASE_I_LV = BASE_POWER/BASE_VOLTAGE_LV #Amps    2.5000  2500

def fetch_base_z_from_line(DATA, l):
    LBUS,SUBS,SLACK,LINES,LINES_OPT,N_PERIODS = DATA
    sending_bus = LINES[l].to_bus
    try :
        voltage_level = LBUS[sending_bus].voltage_level
    except :
        try :
            voltage_level = SUBS[sending_bus].voltage_level 
        except:
            voltage_level = SLACK[sending_bus].voltage_level

    if voltage_level == 70000:
        return BASE_Z_HV
    elif voltage_level == 15000:
        return BASE_Z_MV
    else:
        return BASE_Z_LV
    
def fetch_base_i_from_line(DATA, l):
    LBUS,SUBS,SLACK,LINES,LINES_OPT,N_PERIODS = DATA
    sending_bus = LINES[l].to_bus
    try :
        voltage_level = LBUS[sending_bus].voltage_level
    except :
        try :
            voltage_level = SUBS[sending_bus].voltage_level 
        except:
            voltage_level = SLACK[sending_bus].voltage_level

    if voltage_level == 70000:
        return BASE_I_HV
    elif voltage_level == 15000:
        return BASE_I_MV
    else:
        return BASE_I_LV
    

def is_line_from_LV_load(DATA, l):
    LBUS,SUBS,SLACK,LINES,LINES_OPT,N_PERIODS = DATA
    receving_bus = LINES[l].from_bus
    try:
        LBUS[receving_bus]
        if LBUS[receving_bus].b_type == "LV_load":
            return True
        else:
            return False
    except:
        return False
    
def is_line_to_LV_load(DATA, l):
    LBUS,SUBS,SLACK,LINES,LINES_OPT,N_PERIODS = DATA
    receving_bus = LINES[l].to_bus
    try:
        LBUS[receving_bus]
        if LBUS[receving_bus].b_type == "LV_load":
            return True
        else:
            return False
    except:
        return False
        

def obtain_coef(n):
    # Adjust the angle to rotate the first vertex to the positive y-axis
    angle_offset = math.pi / 2  # 90 degrees in radians

    # Compute coefficients for n-sided polygon with the first vertex on the positive y-axis
    coefficients = [(math.cos((k * 2 * math.pi / n) + angle_offset), 
                     math.sin((k * 2 * math.pi / n) + angle_offset)) 
                    for k in range(n)]
    
    # Compute the correct scale factor
    scale_factor = 1 / math.cos(math.pi / n)

    return coefficients, scale_factor


coefficients, scale_factor = obtain_coef(10)
#print(coefficients)

def log_interval_length(b, n, i, base=2.72, epsilon=0.1, a=0):
    """
    Computes the length of the i-th interval when dividing the range [a, b] logarithmically into n intervals.
    
    The division follows a logarithmic scale, meaning each interval grows exponentially.
    The interval index `i` starts from 1 (not 0), and the function returns the size of the i-th interval.

    Parameters:
    - a (float): The start of the range (must be > 0 for logarithmic scaling).
    - b (float): The end of the range (must be > a).
    - n (int): The total number of intervals.
    - i (int): The interval index (1-based, meaning it ranges from 1 to n).
    - base (float, optional): The logarithm base (default is 10). Use `np.e` for natural logarithm.

    Returns:
    - float: The length of the i-th interval.

    Raises:
    - ValueError: If `i` is not in the range [1, n].

    Example Usage:
    ```python
    a, b, n = 1, 1000, 5
    for i in range(1, n + 1):
        print(f"Interval {i}: Length = {log_interval_length(a, b, n, i)}")
    ```
    """
    if i < 1 or i > n:
        raise ValueError("Index i must be in range 1 to n")
    
    a = a + epsilon
    b = b + epsilon

    log_a = np.log(a) / np.log(base)  # Log-scale start
    log_b = np.log(b) / np.log(base)  # Log-scale end
    
    delta_L = (log_b - log_a) / n  # Logarithmic step size
    
    x_start = base ** (log_a + (i - 1) * delta_L)  # Start of interval i
    x_end = base ** (log_a + i * delta_L)  # End of interval i
    
    return x_end - x_start  # Interval length

import re

import re

import re

def parse_solver_log(log_file):
    # Open and read the log file
    with open(log_file, 'r') as f:
        log_lines = f.readlines()

    # Initialize variables
    execution_time = None
    solver_status = None
    gap = None
    best_objective = None
    best_bound = None
    warnings = []

    # Loop through each line to parse the information
    for line in log_lines:
        # Parse execution time (e.g., 'in 97.85 seconds')
        if "seconds" in line:
            time_match = re.search(r'(\d+\.\d+)\s+seconds', line)
            if time_match:
                execution_time = float(time_match.group(1))
        
        # Check for solver status (Optimal solution found)
        if "Optimal solution found" in line:
            solver_status = "Optimal"
        
        # Look for gap information (e.g., 'gap 0.0983%')
        gap_match = re.search(r'gap\s*([\d\.]+)%', line)  # For "gap 0.0983%"
        if gap_match:
            gap = float(gap_match.group(1))  # The gap value without the '%' symbol
        
        # Look for best objective and best bound
        best_objective_match = re.search(r'Best objective\s*([\d\.]+)', line)
        if best_objective_match:
            best_objective = float(best_objective_match.group(1))
        
        best_bound_match = re.search(r'best bound\s*([\d\.]+)', line)
        if best_bound_match:
            best_bound = float(best_bound_match.group(1))
        
        # Look for warnings or other messages
        if "Warning" in line:
            warnings.append(line.strip())
    
    return execution_time, solver_status, gap, best_objective, best_bound, warnings










