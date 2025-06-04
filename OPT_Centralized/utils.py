import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import re

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

################################################################################################################

def fetch_base_z_from_line(DATA, l):
    
    LBUS,SUBS,SLACK,LINES,LINES_OPT,N_PERIODS = DATA
    BUS = LBUS | SUBS | SLACK

    sending_bus = LINES[l].to_bus
    receving_bus = LINES[l].from_bus

    if BUS[sending_bus].voltage_level >= BUS[receving_bus].voltage_level:  
        voltage_level = BUS[receving_bus].voltage_level
    else:
        voltage_level = BUS[sending_bus].voltage_level

    if voltage_level == 70000:
        return BASE_Z_HV
    elif voltage_level == 15000:
        return BASE_Z_MV
    else:
        return BASE_Z_LV
    
################################################################################################################

def fetch_base_i_from_line(DATA, l):
    LBUS,SUBS,SLACK,LINES,LINES_OPT,N_PERIODS = DATA
    BUS = LBUS | SUBS | SLACK

    sending_bus = LINES[l].to_bus
    receving_bus = LINES[l].from_bus

    if BUS[sending_bus].voltage_level >= BUS[receving_bus].voltage_level:  
        voltage_level = BUS[receving_bus].voltage_level
    else:
        voltage_level = BUS[sending_bus].voltage_level

    if voltage_level == 70000:
        return BASE_I_HV
    elif voltage_level == 15000:
        return BASE_I_MV
    else:
        return BASE_I_LV
    
################################################################################################################

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
    
################################################################################################################

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
    
################################################################################################################

def is_line_to_or_from_load(DATA, l):
    LBUS,SUBS,SLACK,LINES,LINES_OPT,N_PERIODS = DATA
    BUSES = LBUS | SUBS | SLACK
    receving_bus = LINES[l].to_bus
    sending_bus = LINES[l].from_bus
    type_1 = BUSES[receving_bus].b_type
    type_2 = BUSES[sending_bus].b_type 
    if type_1 in ["LV_load", "MV_load"] or type_2 in ["LV_load", "MV_load"]:
        return True
    else:   
        return False
        
################################################################################################################

def obtain_coef(n):
    # Adjust the angle to rotate the first vertex to the positive y-axis
    angle_offset = math.pi / 2  # 90 degrees in radians

    # Compute coefficients for n-sided polygon with the first vertex on the positive y-axis
    coefficients = [(round(math.cos((k * 2 * math.pi / n) + angle_offset), 6),  
                    round(math.sin((k * 2 * math.pi / n) + angle_offset), 6))  
                    for k in range(n)]
    
    # Compute the correct scale factor
    scale_factor = 1 / math.cos(math.pi / n)

    return coefficients, scale_factor

################################################################################################################

def log_interval_length(b, n, i, base=2.72, epsilon=0.01, a=0):
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

################################################################################################################

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

################################################################################################################

def get_weights(p, weights):
    day = int(math.trunc((p-1)/24))
    return weights[day]








