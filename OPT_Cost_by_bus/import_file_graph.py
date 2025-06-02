import random
import csv
import math
import copy
from dataclasses import dataclass
import pandas as pd

from collections import defaultdict
from param import *
from pathlib import Path

import re
import pandas as pd



current_file = Path(__file__)
BASE_DIR = current_file.parent.parent

@dataclass
class Conductor:
    code_word: str
    q_mm2: float
    r_per_km: float
    xl_per_km: float
    imax_kA: float
    cost_keur_per_km: float

@dataclass
class Bus:
    bus_id: int
    b_type: str
    voltage_level: float
    district: str
    surface: float
    load_kW: list[float]
    load_kVAR: list[float]
    x_coord: float
    y_coord: float
    vehicle_location: list[float] = None
    vehicle_consumption: list[float] = None

@dataclass
class Substation:
    substation_id: int
    b_type: str
    voltage_level: float
    district: str
    max_capacity: float
    x_coord: float
    y_coord: float

@dataclass
class Line:
    line_id: str
    from_bus: int
    to_bus: int
    length: float

@dataclass
class EV:
    def __init__(self, capacity: float, max_power: float, location: list, consumption: list):
        self.capacity = capacity
        self.max_power = max_power
        self.location = location
        self.power_consumption = consumption

# Define the Building class to store data
class Building:
    def __init__(self, building_id, y, x, L, W, btype, district_name, voltage_rms):
        self.building_id = building_id
        self.position = (y, x)
        self.size = (L, W)
        self.type = btype
        self.district = district_name
        self.voltage_rms = voltage_rms
        self.active_power = None
        self.reactive_power = None
        self.heating_power = None
        self.cooling_power = None


    def __repr__(self):
        return f"Building(ID={self.building_id}, Position={self.position}, Voltage RMS={self.voltage_rms}, Active Power={self.active_power}, Reactive Power={self.reactive_power}, Heating Power={self.heating_power}, Cooling Power={self.cooling_power})"
    
    def set_power(self, **kwargs):
        """
        Set multiple power-related attributes at once.
        Example:
        building.set_power(active_power=[100, 120], reactive_power=[50, 60])
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

# Function to process HTML file and extract building data
def extract_building_data_from_file(file_path):
    # Open the file with UTF-8 encoding
    with open(file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()


    # Regular expression to match Building ID, Position (y,x), and Voltage RMS
    pattern = (
        r'"hovertemplate":"Building ID = (\d+).*?'  # Building ID
        r'Position \(y,x\) = \((\d+),(\d+)\).*?'   # Position (y, x)
        r'Building L,W =(\d+) x (\d+) .*?'         # (L, W) dimensions
        r'Type=([^\\]+).*?'                        # Type of the building
        r'District Name=([^\\]+).*?'               # District Name
        r'Voltage RMS=(\d+\.\d+)'                  # Voltage RMS
        )
    
    # Create an empty dictionary to store the results
    building_data = {}


    for match in re.finditer(pattern, html_content):
        building_id = int(match.group(1))
        y, x = int(match.group(2)), int(match.group(3))
        L, W = int(match.group(4)), int(match.group(5))
        building_type = match.group(6).strip()
        district_name = match.group(7).strip()
        voltage_rms = float(match.group(8))

        
        # Create a new Building object and add it to the dictionary
        building_data[int(building_id)] = Building(building_id, y, x, L, W, building_type, district_name, voltage_rms)

    return building_data





# Function to load and process the Excel data and update the existing buildings dictionary
def update_buildings_with_power_data(file_path, buildings, N_PERIODS_MAX, START_N):
    # Load the sheets into a dictionary
    sheets = pd.read_excel(file_path, sheet_name=None)  # Load all sheets as a dictionary

    # Extract the sheet names (each corresponding to a power type)
    sheet_names = sheets.keys()
    irradiation = []
    # Iterate over each sheet (representing a power type)
    for sheet_name in sheet_names:
        df = sheets[sheet_name]

        # Extract the Building IDs from the first row (starting from the second column)
        building_ids = df.columns[:]

        # Process the data for each building
        for building_id in building_ids:

            if building_id == "ghi":
                irradiation = df[building_id].dropna()  # Drop NaN values
                irradiation = irradiation[START_N:START_N+N_PERIODS_MAX].reset_index(drop=True)

            # Remove the "B" prefix from the building_id in the Excel sheet
            numeric_building_id = building_id.lstrip("B")
            try:
                numeric_building_id = int(numeric_building_id)
            except ValueError:
                # Skip this building ID if it is not a valid integer
                continue
            # Check if the building already exists in the buildings dictionary
            if numeric_building_id in buildings:
                # Extract the data for this building from the current sheet
                building_data = df[building_id].dropna()  # Drop NaN values
                building_data = building_data
                if len(building_data) >= N_PERIODS_MAX+START_N:
                    building_data = building_data[START_N:START_N+N_PERIODS_MAX].reset_index(drop=True)
                # Update the building object with the power data
                if sheet_name == "Electricity (kWh)":
                    buildings[numeric_building_id].set_power(active_power=building_data.tolist())
                elif sheet_name == "Electricity (kvarh)":
                    buildings[numeric_building_id].set_power(reactive_power=building_data.tolist())
                elif sheet_name == "Heat (kWh)":
                    buildings[numeric_building_id].set_power(heating_power=building_data.tolist())
                elif sheet_name == "Cold (kWh)":
                    buildings[numeric_building_id].set_power(cooling_power=building_data.tolist())

    return buildings, irradiation

import os

def find_city_files(city_name, folder_path):
    city_name_formatted = city_name.replace(" ", "_")  # Match file naming convention
    html_file = None
    excel_file = None

    # Scan folder and categorize files
    for file in os.listdir(folder_path):
        if city_name_formatted in file:
            if file.endswith(".html"):
                html_file = file
            elif file.endswith(".xlsx"):
                excel_file = file

    if html_file and excel_file:
        return [html_file, excel_file]
    else:
        return f"Expected 1 HTML and 1 Excel file, found: {html_file}, {excel_file}"
    

def get_index_from_date(START_DATE):    
    day, month, time = START_DATE
    
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    
    n = sum(days_in_month[:month - 1])
    n = n + day - 1
    n = n * 24
    n = n + time
    
    return n

def extract(folder_path, city, N_PERIODS_MAX, START_DATE):
    
    file_names = find_city_files(city, folder_path)
    START_N = get_index_from_date(START_DATE)

    html_path = folder_path / file_names[0]
    print("Scapring the data from the HTML file")
    building_data = extract_building_data_from_file(html_path)
    print("Data scraped successfully!")


    excel_path = folder_path / file_names[1]
    print("Updating the buildings with power data from the Excel file")
    updated_buildings, irradiation = update_buildings_with_power_data(excel_path, building_data, N_PERIODS_MAX, START_N)
    print("Buildings updated successfully!")

    return updated_buildings, irradiation


def load_conductors_csv(file_path = BASE_DIR / "Campus data" / "MyCampus" / "conductors.csv"):
    conductors_dict = {}
    
    with open(file_path, mode='r', newline='') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        
        for row in csv_reader:
            conductor = Conductor(
                code_word=row['Code word'],
                q_mm2=float(row['q [mm2]']),
                r_per_km=float(row['r [ohm/km]']),
                xl_per_km=float(row['xl [ohm/km]']),
                imax_kA=float(row['imax [kA]']),
                cost_keur_per_km=float(row['cost [keur/km]'])
            )
            conductors_dict[row['Code word']] = conductor  # Store in dict by code_word
            
    return conductors_dict


def load_bus(city, folder_path= BASE_DIR / "Campus data" / "UpdatedData"):
    random.seed(32)
    START_DATE = (1,1,0)  #Day, Month, Hour
    N_PERIODS_MAX = 365 * 24

    if city == "Mycampus":
        
        N_PERIODS = N_PERIODS_MAX
        csv_path = BASE_DIR / "Campus data" / "MyCampus" / "Mycampus2.csv"
    
        slack_dict = {}
        buses_dict = {}
        substations_dict = {}

        # Load data from CSV
        df = pd.read_csv(csv_path)

        # Clean data (ensure all relevant columns exist and strip spaces)
        df.columns = df.columns.str.strip()
        df["District"] = df["District"].fillna("Unknown").astype(str).str.strip()
        df["Type"] = df["Type"].fillna("Unknown").astype(str).str.strip()
        df["Position"] = df["Position"].astype(str).str.strip()

        # Extract coordinates (ensure negative numbers in the coordinates are handled)
        df[['X', 'Y']] = df['Position'].str.extract(r'\((-?\d+);(-?\d+)\)').astype(float)

        # Loop through the dataframe and classify as buses or substations
        for _, row in df.iterrows():
            bus_id = int(row["Bus ID"])  # Ensure Bus ID is unique with offset if necessary
            bus_type = row["Type"]
            x, y = row["X"], row["Y"]

            # Check if it is a substation or bus
            if bus_type in ["HV_sub"]:  # Substation
                substation = Substation(
                    substation_id=bus_id,
                    b_type=row["Type"],
                    voltage_level=float(row["Voltage"]),
                    district=row["District"],
                    max_capacity=1000000000,  # You can define this as needed
                    x_coord=x,
                    y_coord=y
                )
                slack_dict[bus_id] = substation

        
            elif bus_type in ["MV_sub"]:
                substation = Substation(
                    substation_id=bus_id,
                    b_type=row["Type"],
                    voltage_level=float(row["Voltage"]),
                    district=row["District"],
                    max_capacity=100000000,  # You can define this as needed
                    x_coord=x,
                    y_coord=y
                )
                substations_dict[bus_id] = substation


            else:
                if N_PERIODS == 1:
                    load_kW = []
                    load_kVAR = []
                    load_kW.append(float(row["Active Power"]))
                    load_kVAR.append(float(row["Reactive Power"]))
                else:
                    load_kW = [random.uniform(0.8*float(row["Active Power"]), 1.2*float(row["Active Power"])) for _ in range(N_PERIODS)]
                    load_kVAR = [random.uniform(0.8*float(row["Reactive Power"]), 1.2*float(row["Reactive Power"])) for _ in range(N_PERIODS)]


                bus = Bus(
                    bus_id=bus_id,
                    b_type=row["Type"],
                    voltage_level=float(row["Voltage"]),
                    district=row["District"],
                    surface=random.uniform(40, 60),  # Random surface area between 40 and 60 sq. m
                    load_kW=load_kW,
                    load_kVAR=load_kVAR,
                    x_coord=x,
                    y_coord=y
                )
                buses_dict[bus_id] = bus

        
        def extract_column_g(start_index, csv_filename= BASE_DIR / "Campus data" / "MyCampus" / "Irradiation.csv"):
            column_g = []
            with open(csv_filename, newline='') as csvfile:
                reader = csv.reader(csvfile)
                
                # Skip metadata lines
                for _ in range(8):
                    next(reader)
                
                # Read header row
                header = next(reader)
                g_index = header.index("G(i)")
                
                # Extract values from column G
                for index, row in enumerate(reader):
                    if index < start_index:
                        continue  # Skip rows until reaching start_index

                    if len(column_g)  >= N_PERIODS:
                        break
                    column_g.append(float(row[g_index]))
            
            return column_g
        
        start_index = get_index_from_date(START_DATE)
        irradiation = extract_column_g(start_index)


        return buses_dict, substations_dict, slack_dict, irradiation
    
    elif city== "Newcampus":
        def get_bus_load_data(bus_id, excel_path=Path("Campus data") / "MyCampus" / "Newcampus.xlsx"):

            """Returns active power (kW) and power factor vectors for a given bus ID from the Excel file.
            
            Args:
                bus_id (int): The bus ID to look up in the Excel file
                excel_path (Path): Path to the Excel file
            
            Returns:
                tuple: (active_power_list, power_factor_list) - lists of values for each day in the file"""
            
            try:
                # Read the Excel file with multi-index header
                excel_data = pd.read_excel(excel_path, header=[0,1])
                
                # Initialize empty lists
                active_power = []
                power_factor = []
                
                # Check if this bus_id exists in the data
                bus_cols = [col for col in excel_data.columns if str(bus_id) == str(col[0])]
                
                if not bus_cols:
                    raise ValueError(f"Bus ID {bus_id} not found in Excel file")
                
                # Get the active power and PF columns for this bus
                active_col = next(col for col in bus_cols if col[1] == 'Active')
                pf_col = next(col for col in bus_cols if col[1] == 'PF')
                
                # Extract the values
                active_power = excel_data[active_col].tolist()
                power_factor = excel_data[pf_col].tolist()
                
                return active_power, power_factor
            
            except Exception as e:
                print(f"Error processing bus {bus_id}: {str(e)}")
                return [], []
        

        def create_yearly_load_profile(active_power, reactive_power):
            """
            Creates a yearly load profile from 8 days of data (week/weekend for 4 seasons).
            
            Args:
                active_power: List of 192 values (24h × 8 days) in order:
                            [Winter weekday, Winter weekend,
                            Spring weekday, Spring weekend,
                            Summer weekday, Summer weekend,
                            Autumn weekday, Autumn weekend]
                power_factor: Corresponding power factors
            
            Returns:
                tuple: (yearly_active, yearly_reactive) - 8760 values each (24×365)
            """
            # Convert to numpy arrays for easier manipulation
            active_power = np.array(active_power)
            reactive_power = np.array(reactive_power)
            
            # Reshape to 8 days of 24 hours each
            daily_active = active_power.reshape(8, 24)
            daily_reactive = reactive_power.reshape(8,24)
            
            # Define the seasons structure
            seasons = {
                'winter': {'weekday': 0, 'weekend': 1, 'weeks': 13},
                'spring': {'weekday': 2, 'weekend': 3, 'weeks': 13},
                'summer': {'weekday': 4, 'weekend': 5, 'weeks': 13},
                'autumn': {'weekday': 6, 'weekend': 7, 'weeks': 13}
            }
            
            # Initialize yearly profiles
            yearly_active = []
            yearly_reactive = []
            
            # Build each season's profile
            for season in ['winter', 'spring', 'summer', 'autumn']:
                weekday_idx = seasons[season]['weekday']
                weekend_idx = seasons[season]['weekend']
                
                # Add 13 weeks of this season (5 weekdays + 2 weekend days each)
                for week in range(seasons[season]['weeks']):
                    # Add 5 weekdays
                    for day in range(5):
                        yearly_active.extend(daily_active[weekday_idx])
                        yearly_reactive.extend(daily_reactive[weekday_idx])
                    
                    # Add 2 weekend days
                    for day in range(2):
                        yearly_active.extend(daily_active[weekend_idx])
                        yearly_reactive.extend(daily_reactive[weekend_idx])
            
            # Add one extra winter weekday (to reach 365 days)
            yearly_active.extend(daily_active[seasons['winter']['weekday']])
            yearly_reactive.extend(daily_reactive[seasons['winter']['weekday']])
            
            # Convert back to lists if needed
            yearly_active = list(yearly_active)
            yearly_reactive = list(yearly_reactive)
            
            # Verify we have exactly 8760 values (24×365)
            assert len(yearly_active) == 8760, f"Expected 8760 hours, got {len(yearly_active)}"
            assert len(yearly_reactive) == 8760, f"Expected 8760 hours, got {len(yearly_reactive)}"
            
            return yearly_active, yearly_reactive


        N_PERIODS = N_PERIODS_MAX
        csv_path = BASE_DIR / "Campus data" / "MyCampus" / "Newcampus.csv"
    
        slack_dict = {}
        buses_dict = {}
        substations_dict = {}

        # Load data from CSV
        df = pd.read_csv(csv_path)

        # Clean data (ensure all relevant columns exist and strip spaces)
        df.columns = df.columns.str.strip()
        df["District"] = df["District"].fillna("Unknown").astype(str).str.strip()
        df["Type"] = df["Type"].fillna("Unknown").astype(str).str.strip()
        df["Position"] = df["Position"].astype(str).str.strip()

        # Extract coordinates (ensure negative numbers in the coordinates are handled)
        df[['X', 'Y']] = df['Position'].str.extract(r'\((-?\d+);(-?\d+)\)').astype(float)

        # Loop through the dataframe and classify as buses or substations
        for _, row in df.iterrows():
            bus_id = int(row["Bus ID"])  # Ensure Bus ID is unique with offset if necessary
            bus_type = row["Type"]
            x, y = row["X"], row["Y"]

            # Check if it is a substation or bus
            if bus_type in ["HV_sub"]:  # Substation
                substation = Substation(
                    substation_id=bus_id,
                    b_type=row["Type"],
                    voltage_level=float(row["Voltage"]),
                    district=row["District"],
                    max_capacity=1000000000,  # You can define this as needed
                    x_coord=x,
                    y_coord=y
                )
                slack_dict[bus_id] = substation

        
            elif bus_type in ["MV_sub"]:
                substation = Substation(
                    substation_id=bus_id,
                    b_type=row["Type"],
                    voltage_level=float(row["Voltage"]),
                    district=row["District"],
                    max_capacity=100000000,  # You can define this as needed
                    x_coord=x,
                    y_coord=y
                )
                substations_dict[bus_id] = substation


            else:
                active_power, power_factor = get_bus_load_data(bus_id)
                reactive_power = []
                for ap, pf in zip(active_power, power_factor):
                    if pf != 1:
                        s = ap/pf
                        reactive_power.append((s**2-ap**2)**0.5)
                    else:
                        reactive_power.append(0)

                yearly_active, yearly_reactive = create_yearly_load_profile(active_power, reactive_power)

                bus = Bus(
                    bus_id=bus_id,
                    b_type=row["Type"],
                    voltage_level=float(row["Voltage"]),
                    district=row["District"],
                    surface=random.uniform(40, 60),  # Random surface area between 40 and 60 sq. m
                    load_kW=yearly_active,
                    load_kVAR=yearly_reactive,
                    x_coord=x,
                    y_coord=y
                )
                buses_dict[bus_id] = bus

        
        def extract_column_g(start_index, csv_filename= BASE_DIR / "Campus data" / "MyCampus" / "Irradiation.csv"):
            column_g = []
            with open(csv_filename, newline='') as csvfile:
                reader = csv.reader(csvfile)
                
                # Skip metadata lines
                for _ in range(8):
                    next(reader)
                
                # Read header row
                header = next(reader)
                g_index = header.index("G(i)")
                
                # Extract values from column G
                for index, row in enumerate(reader):
                    if index < start_index:
                        continue  # Skip rows until reaching start_index

                    if len(column_g)  >= N_PERIODS:
                        break
                    column_g.append(float(row[g_index]))
            
            return column_g
        
        start_index = get_index_from_date(START_DATE)
        irradiation = extract_column_g(start_index)


        return buses_dict, substations_dict, slack_dict, irradiation
    
    else:

        updated_buildings, irradiation = extract(folder_path, city, N_PERIODS_MAX, START_DATE)
        slack_dict = {}
        buses_dict = {}
        substations_dict = {}
        current_id = 0

        # Loop through the updated_buildings to update them with power data
        for building_id, building in updated_buildings.items():
            
            current_id = max(current_id,building.building_id)

            if building.active_power is None:
                # This means the building is a substation
                # Assuming substation data (substation_id, voltage_level, etc.) is available in the building object
                substation = Substation(
                    substation_id=building.building_id,  # Using ID from the building
                    b_type='HV_sub',
                    voltage_level=building.voltage_rms,  # Assuming 'Voltage RMS' field is there
                    district=None,
                    max_capacity=10000000,  # Set as None, or find the relevant data field
                    x_coord=building.position[0],  # Using Position as (x, y)
                    y_coord=building.position[1]
                )
                
                slack_dict[building_id] = substation


            else:
                # This means the building is a load bus not in MYCAMPUS
                # Now, the active and reactive power are lists in 'building.active_power' and 'building.reactive_power'
                load_kW = building.active_power  # Keep the active power as a list
                load_kVAR = building.reactive_power  # Keep the reactive power as a list
                voltage_level = building.voltage_rms
                if voltage_level == 400:
                    b_type = 'LV_load'
                else:
                    b_type = 'MV_load'
                bus = Bus(
                    bus_id=building.building_id,  # Using building's ID
                    b_type = b_type,
                    voltage_level=voltage_level,  # Using 'Voltage RMS'
                    district = building.district,
                    surface=building.size[0]*building.size[1],
                    load_kW=load_kW,  # Active power as a list
                    load_kVAR=load_kVAR,  # Reactive power as a list
                    x_coord=building.position[0],  # Using Position (x, y)
                    y_coord=building.position[1]
                )

                
                
                buses_dict[building_id] = bus


        for district in set(b.district for b in updated_buildings.values() if b.district and b.district != 'TFO'):
            # Find the boundary for this district (min and max x, y)
            district_buildings = [b for b in updated_buildings.values() if b.district == district]
            min_x = min(b.position[0] for b in district_buildings)
            max_x = max(b.position[0] for b in district_buildings)
            min_y = min(b.position[1] for b in district_buildings)
            max_y = max(b.position[1] for b in district_buildings)

            # Generate 3 random locations within the boundary
            for _ in range(3):
                random_x = random.uniform(min_x, max_x)
                random_y = random.uniform(min_y, max_y)

                mv_substation = Substation(
                    substation_id=current_id+1,  # Unique ID for each MV substation
                    b_type='MV_sub',
                    voltage_level=15000,  # Use the same voltage level as the building
                    district=district,
                    max_capacity=1000000,  # Default capacity
                    x_coord=random_x,
                    y_coord=random_y
                )
                substations_dict[current_id+1] = mv_substation
                current_id += 1

        return buses_dict, substations_dict, slack_dict, irradiation


import networkx as nx
from collections import defaultdict

def calculate_distance(bus1, bus2):
    """Calculate Euclidean distance between two buses."""
    return ((bus2.x_coord - bus1.x_coord)**2 + (bus2.y_coord - bus1.y_coord)**2)**0.5

def build_graph(BUS):
    """Builds a NetworkX graph based on the connection rules."""
    G = nx.Graph()
    
    # Group buses by district
    buses_by_district = defaultdict(lambda: defaultdict(list))
    for bus in BUS.values():
        buses_by_district[bus.district][bus.b_type].append(bus)
    
    # Rule 1: Connect every HV_sub to every MV_sub
    hv_subs = [bus for bus in BUS.values() if bus.b_type == 'HV_sub']
    mv_subs = [bus for bus in BUS.values() if bus.b_type == 'MV_sub']
    for hv_sub in hv_subs:
        for mv_sub in mv_subs:
            length = calculate_distance(hv_sub, mv_sub)
            G.add_edge(hv_sub.substation_id, mv_sub.substation_id, weight=length)
    
    # Rules 2 & 3: Connect MV_sub to MV_load and LV_load in the same district
    for district, types in buses_by_district.items():
        mv_subs_district = types.get('MV_sub', [])
        mv_loads_district = types.get('MV_load', [])
        lv_loads_district = types.get('LV_load', [])
        
        for mv_sub in mv_subs_district:
            # Connect to MV_loads
            for mv_load in mv_loads_district:
                length = calculate_distance(mv_sub, mv_load)
                G.add_edge(mv_sub.substation_id, mv_load.bus_id, weight=length)
            # Connect to LV_loads
            for lv_load in lv_loads_district:
                length = calculate_distance(mv_sub, lv_load)
                G.add_edge(mv_sub.substation_id, lv_load.bus_id, weight=length)
    
    # Rule 4: Connect each MV_load to 3 closest MV_loads in the same district
    for district, types in buses_by_district.items():
        mv_loads = types.get('MV_load', [])
        edges = set()
        for i, bus in enumerate(mv_loads):
            distances = []
            for j, other_bus in enumerate(mv_loads):
                if i == j:
                    continue
                dist = calculate_distance(bus, other_bus)
                pair = tuple(sorted([bus.bus_id, other_bus.bus_id]))
                distances.append((dist, pair))
            distances.sort()
            for d, pair in distances[:3]:
                edges.add(pair)
        for u, v in edges:
            bus_u = BUS[u]
            bus_v = BUS[v]
            G.add_edge(u, v, weight=calculate_distance(bus_u, bus_v))
    
    # Rule 5: Connect each LV_load to 3 closest LV_loads in the same district
    for district, types in buses_by_district.items():
        lv_loads = types.get('LV_load', [])
        edges = set()
        for i, bus in enumerate(lv_loads):
            distances = []
            for j, other_bus in enumerate(lv_loads):
                if i == j:
                    continue
                dist = calculate_distance(bus, other_bus)
                pair = tuple(sorted([bus.bus_id, other_bus.bus_id]))
                distances.append((dist, pair))
            distances.sort()
            for d, pair in distances[:3]:
                edges.add(pair)
        for u, v in edges:
            bus_u = BUS[u]
            bus_v = BUS[v]
            G.add_edge(u, v, weight=calculate_distance(bus_u, bus_v))
    
    # Rule 6: Connect MV_subs to each other in the same district
    for district, types in buses_by_district.items():
        mv_subs = types.get('MV_sub', [])
        for i in range(len(mv_subs)):
            for j in range(i+1, len(mv_subs)):
                mv1 = mv_subs[i]
                mv2 = mv_subs[j]
                length = calculate_distance(mv1, mv2)
                G.add_edge(mv1.substation_id, mv2.substation_id, weight=length)
    
    return G

def load_lines(BUS):
    """Generates candidate lines using MSTs for each substation deactivation."""
    G = build_graph(BUS)
    
    # Identify substations to deactivate (HV_sub and MV_sub)
    substations_to_deactivate = [
        bus.substation_id for bus in BUS.values() 
        if bus.b_type in ['HV_sub', 'MV_sub']
    ]
    
    candidate_edges = set()
    
    for s in substations_to_deactivate:
        G_copy = G.copy()
        # Remove edges connected to the deactivated substation
        edges_to_remove = list(G_copy.edges(s))
        G_copy.remove_edges_from(edges_to_remove)
        # Compute MST
        mst_edges = nx.minimum_spanning_edges(G_copy, weight='weight', data=False)
        # Store edges using frozenset to avoid duplicates
        for u, v in mst_edges:
            candidate_edges.add(frozenset({u, v}))
    
    # Convert to list of tuples and create lines
    lines_dict = {}
    line_id = 0
    for edge in candidate_edges:
        u, v = tuple(edge)
        bus_u = BUS[u]
        bus_v = BUS[v]
        length = calculate_distance(bus_u, bus_v)
        line_obj = Line(
            line_id=line_id,
            from_bus=u,
            to_bus=v,
            length=length
        )
        lines_dict[line_id] = line_obj
        line_id += 1
    
    return lines_dict


def update_bus_loads(LBUS, stages):
    """
    Update the list of buses for each stage.

    Parameters:
      - LBUS: dict of Bus objects keyed by bus_id
      - stages: list of stage numbers (e.g., [0, 1, 2])
      
    Returns:
      A dictionary mapping each stage to the modified LBUS dictionary.
    """
    # Initialize output dictionary
    stage_outputs = {}

    # Mapping to keep track if a bus has EV or HP. Format: {bus_id: {"ev": bool, "hp": bool}}
    bus_has_device = {bus.bus_id: {"hp": False} for bus in LBUS.values()}

    # Stage 0: copy original dictionary
    stage_outputs[0] = copy.deepcopy(LBUS)

    # For each subsequent stage
    for stage in stages:
        if stage == 0:
            continue  # Already processed stage 0

        # Build a map from actual district names to district_thresholds keys
        unique_districts = sorted(set(bus.district for bus in LBUS.values()))
        district_name_to_threshold_key = {
            name: str(i + 1) for i, name in enumerate(unique_districts)
        }

        # Process a new stage; we update the same LBUS dict in-place.
        for bus in LBUS.values():
            # Adjust load based on voltage level
            if bus.voltage_level == 15000:
                factor = industrial_growth_demand
            else:  # assume voltage level is 400 if not 15000
                factor = residential_growth_demand

            # Multiply every element in load_kW and load_kVAR by the factor
            bus.load_kW = [value * factor for value in bus.load_kW]
            bus.load_kVAR = [value * factor for value in bus.load_kVAR]

            """# Get district thresholds for EV and HP
            district = bus.district
            # Map district name to threshold key
            threshold_key = district_name_to_threshold_key.get(district)
            thresholds = district_thresholds.get(threshold_key, {"hp": 0.0})

            # For HP
            if not bus_has_device[bus.bus_id]["hp"]:
                rand_hp = random.random()
                if rand_hp < thresholds["hp"]:
                    bus_has_device[bus.bus_id]["hp"] = True
                    bus.load_kW = [
                        lw + hp_daily_load[i % 24] for i, lw in enumerate(bus.load_kW)
                    ]
                    bus.load_kVAR = [
                        lv + hp_daily_load[i % 24] for i, lv in enumerate(bus.load_kVAR)
                    ]"""

        # Save a deep copy of the updated LBUS for the current stage
        stage_outputs[stage] = copy.deepcopy(LBUS)
    print(bus_has_device)
    return stage_outputs


import random
import numpy as np

def load_ev(LBUS, EV_option, max_power=22) -> dict[int, EV]:
    T = 24
    if EV_option == False:
        for bus in LBUS.values():
            if bus.b_type == 'MV_load':
                continue

            location = [np.nan] * T
            consumption = [np.nan] * T

            bus.vehicle_location = location
            bus.vehicle_consumption = consumption

            return {}
        
    profiles_proba = {
        'stay': 0,
        'morning': 0,
        'evening': 0,
        'full_day': 1
    }
    profiles = ['stay', 'morning', 'evening', 'full_day']
    total = sum(profiles_proba[p] for p in profiles)
    weights = [profiles_proba[p] / total for p in profiles]
  # Hourly resolution for one day
    mv_load_counts = defaultdict(int)

    for bus in LBUS.values():
        if bus.b_type == 'MV_load':
            continue

        # Sample profile correctly
        profile = random.choices(profiles, weights=weights, k=1)[0]
        away_bus = random.choice([b for b in LBUS.keys() if b != bus.bus_id and LBUS[b].b_type == 'MV_load'])

        mv_load_counts[away_bus] += 1

        # Initialize
        location = [np.nan] * T
        consumption = [np.nan] * T

        if profile == 'stay':
            # Vehicle never leaves: stays at its home bus all day
            location = [bus.bus_id] * T
        else:
            # Determine departure and return times based on profile
            if profile == 'morning':
                depart = random.randint(6, 8)
                returna = random.randint(10, 12)
            elif profile == 'evening':
                depart = random.randint(11, 13)
                returna = random.randint(16, 18)
            elif profile == 'full_day':
                depart = random.randint(6, 8)
                returna = random.randint(16, 18)

            # Assign two charging events
            consumption[depart] = round(random.uniform(0.1 * max_power, max_power), 2)
            consumption[returna] = round(random.uniform(0.1 * max_power, max_power), 2)

            # Build the location timeline
            for t in range(depart):
                location[t] = bus.bus_id
            location[depart] = np.nan
            for t in range(depart + 1, returna):
                location[t] = away_bus
            location[returna] = np.nan
            for t in range(returna + 1, T):
                location[t] = bus.bus_id

        bus.vehicle_location = location
        bus.vehicle_consumption = consumption

    return mv_load_counts






