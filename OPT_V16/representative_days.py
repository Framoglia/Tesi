import csv
from datetime import datetime, timedelta

def write_csv(LBUS, irradiation, filename):
    # Determine the number of timesteps (should be 365*24)
    n_timesteps = len(irradiation)
    
    # Start datetime: January 1, 2025 at midnight.
    start_dt = datetime(2025, 1, 1, 0, 0, 0)
    
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write header
        writer.writerow(["date", "total load", "irradiation"])
        
        # Loop over each timestep
        for i in range(n_timesteps):
            # Compute current time by adding i hours to start_dt
            current_dt = start_dt + timedelta(hours=i)
            # Format date as "MM/DD HH:MM:SS"
            date_str = current_dt.strftime("%m/%d %H:%M:%S")
            
            # Compute the total load for the timestep:
            # Sum each building's (load_kW + load_kVAR) at index i.
            total_load = 0.0
            for bus in LBUS.values():
                total_load += bus.load_kW[i] + bus.load_kVAR[i]
            
            # Write the row to CSV
            writer.writerow([date_str, total_load, irradiation[i]])


import subprocess

def run_daysxtractor():
    # Define the command and its arguments
    command = [
        "python", 
        "-m", 
        "daysxtractor", 
        "-n", "1",  # number of days
        "-t", "30",  # maximum solving time
        "-s", "gurobi",  # solver
        "-v",  # verbose flag
        "-p", "aggregate demand.csv"  # input CSV file
    ]
    
    # Run the command using subprocess
    try:
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        print("Output:", result.stdout)  # Print the standard output of the command
        print("Error (if any):", result.stderr)  # Print any error output
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Return code: {e.returncode}")
        print(f"Output: {e.output}")
    except Exception as e:
        print(f"Unexpected error: {e}")

import csv
from datetime import datetime, timedelta
import copy

import csv
from datetime import datetime, timedelta
import copy

def extract_representative_days(LBUS, irradiation, rep_days_csv, start_year=2025):
    """
    Extract representative days from original timeseries data.
    
    Parameters:
        LBUS: dict of building objects. Each building must have load_kW and load_kVAR lists.
        irradiation: list of irradiation values (length should be 365*24).
        rep_days_csv: path to CSV file containing representative days.
                      Expected CSV format: header with "Day" (YYYY-MM-DD) and "Weight".
        start_year: the starting year for the time series (default: 2025).
    
    Returns:
        new_LBUS: new dictionary of building objects with load_kW and load_kVAR lists
                  restricted to the representative days.
        new_irradiation: new list of irradiation values for the representative days.
        weights: a list of weights corresponding to each representative day.
    """
    representative_dates = []
    weights = []
    
    # Parse representative days CSV: read date and weight for each representative day.
    with open(rep_days_csv, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            day_str = row["Day"]
            try:
                day_obj = datetime.strptime(day_str, "%Y-%m-%d").date()
                representative_dates.append(day_obj)
            except ValueError as e:
                print(f"Skipping invalid date {day_str}: {e}")
                continue
            
            try:
                weight = float(row["Weight"])
            except ValueError as e:
                print(f"Skipping invalid weight for {day_str}: {e}")
                continue
            weights.append(weight)
    
    # Define the starting date of the original timeseries.
    start_date = datetime(start_year, 1, 1).date()
    
    # Extract irradiation slices for the representative days.
    new_irradiation = []
    for rep_day in representative_dates:
        # Calculate the day offset (each day has 24 hours).
        day_offset = (rep_day - start_date).days
        start_index = day_offset * 24
        end_index = start_index + 24
        new_irradiation.extend(irradiation[start_index:end_index])
    
    # Create new LBUS: for each building, copy the object and slice its load lists.
    new_LBUS = {}
    for key, building in LBUS.items():
        # Create a shallow copy to preserve non-list attributes.
        new_building = copy.copy(building)
        new_load_kW = []
        new_load_kVAR = []
        for rep_day in representative_dates:
            day_offset = (rep_day - start_date).days
            start_index = day_offset * 24
            end_index = start_index + 24
            new_load_kW.extend(building.load_kW[start_index:end_index])
            new_load_kVAR.extend(building.load_kVAR[start_index:end_index])
        new_building.load_kW = new_load_kW
        new_building.load_kVAR = new_load_kVAR
        new_LBUS[key] = new_building

    return new_LBUS, new_irradiation, weights



