import random
import csv
from dataclasses import dataclass
import pandas as pd
from extract_building import extract
from generate_lines import generate_lines

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

def load_conductors_csv(file_path=r"C:\Users\mogli\OneDrive\Desktop\Tesi\Campus data\MyCampus\conductors.csv"):
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


def load_bus(city, N_PERIODS_MAX, START_DATE, folder_path=r"C:\Users\mogli\OneDrive\Desktop\Tesi\Campus data\UpdatedData"):
    if city == "Mycampus":
        random.seed(52)
        N_PERIODS = N_PERIODS_MAX
        csv_path = r"C:\Users\mogli\OneDrive\Desktop\Tesi\Campus data\MyCampus\Mycampus2.csv"
    
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
                    max_capacity=300000000000,  # You can define this as needed
                    x_coord=x,
                    y_coord=y
                )
                slack_dict[bus_id] = substation

        
            elif bus_type in ["MV_sub", "LV_sub"]:
                substation = Substation(
                    substation_id=bus_id,
                    b_type=row["Type"],
                    voltage_level=float(row["Voltage"]),
                    district=row["District"],
                    max_capacity=100000000000,  # You can define this as needed
                    x_coord=x,
                    y_coord=y
                )
                substations_dict[bus_id] = substation



            else:  # Load bus
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

        
        def extract_column_g(csv_filename=r"C:\Users\mogli\OneDrive\Desktop\Tesi\Campus data\MyCampus\Irradiation.csv"):
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
                    if len(column_g)  >= N_PERIODS:
                        break
                    column_g.append(float(row[g_index]))
            
            return column_g
        
        irradiation = extract_column_g()


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
                    max_capacity=10000000000,  # Set as None, or find the relevant data field
                    x_coord=building.position[0],  # Using Position as (x, y)
                    y_coord=building.position[1]
                )
                
                slack_dict[building_id] = substation


            else:
                # This means the building is a bus
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
            random.seed(37)
            for _ in range(2):
                random_x = random.uniform(min_x, max_x)
                random_y = random.uniform(min_y, max_y)

                mv_substation = Substation(
                    substation_id=current_id+1,  # Unique ID for each MV substation
                    b_type='MV_sub',
                    voltage_level=15000,  # Use the same voltage level as the building
                    district=district,
                    max_capacity=10000000000,  # Default capacity
                    x_coord=random_x,
                    y_coord=random_y
                )
                substations_dict[current_id+1] = mv_substation
                current_id += 1

        return buses_dict, substations_dict, slack_dict, irradiation


def load_lines(BUS):
    lines = generate_lines(BUS)

    lines_dict = {}

    for line in lines:
        line_id, from_bus, to_bus = line  # Extract values from tuple/list

        from_x, from_y = BUS[from_bus].x_coord, BUS[from_bus].y_coord
        to_x, to_y = BUS[to_bus].x_coord, BUS[to_bus].y_coord

        length = ((to_x - from_x) ** 2 + (to_y - from_y) ** 2) ** 0.5

        line_obj = Line(
            line_id=line_id,
            from_bus=from_bus,
            to_bus=to_bus,
            length=length
        )
        lines_dict[line_id] = line_obj  # Store in dictionary

    return lines_dict
