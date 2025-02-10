import random
import csv
from dataclasses import dataclass

@dataclass
class Conductor:
    code_word: str
    q_mm2: float
    r_per_km: float
    xl_per_km: float
    imax_kA: float
    cost_keur_per_km: float

def load_conductors_csv(file_path):
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


@dataclass
class Bus:
    bus_id: int
    voltage_level: float
    load_MW: list[float]
    load_MVAR: list[float]
    x_coord: float
    y_coord: float
"""
def load_buses_csv(file_path,N_PERIODS,offset):
    buses_dict = {}
    
    with open(file_path, mode='r', newline='') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        
        for row in csv_reader:
            if N_PERIODS == 1:
                load_MW = float(row['Load [MW]'])
                load_MVAR = float(row['Load [MVAR]'])
            else:
                load_MW = [random.uniform(0,float(row['Load [MW]'])) for _ in range(N_PERIODS)]
                load_MVAR = [random.uniform(0, float(row['Load [MVAR]'])) for _ in range(N_PERIODS)]


            bus = Bus(
                bus_id=int(row['Bus ID'])+offset,
                voltage_level=float(row['Voltage Level [kV]']),
                load_MW= load_MW,
                load_MVAR= load_MVAR,
                x_coord=float(row['x_coord']),
                y_coord=float(row['y_coord'])
            )
            buses_dict[int(row['Bus ID'])+offset] = bus  # Store in dict by bus_id
            
    return buses_dict
"""
@dataclass
class Substation:
    substation_id: int
    voltage_level: float
    max_capacity: float
    x_coord: float
    y_coord: float
"""
def load_substations_csv(file_path):
    substations_dict = {}
    
    with open(file_path, mode='r', newline='') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        
        for row in csv_reader:
            substation = Substation(
                substation_id=int(row['Substation ID']),
                voltage_level=float(row['Voltage Level [kV]']),
                max_capacity=float(row['Max capacyty [MVA]']),
                x_coord=float(row['x_coord']),
                y_coord=float(row['y_coord'])
            )
            substations_dict[int(row['Substation ID'])] = substation  # Store in dict by substation_id
            
    return substations_dict
"""
from extract_building import extract

def load_bus(N_PERIODS_MAX):
    updated_buildings = extract(N_PERIODS_MAX)
    buses_dict = {}
    substations_dict = {}

    # Loop through the updated_buildings to update them with power data
    for building_id, building in updated_buildings.items():
        if building.active_power is None:
            # This means the building is a substation
            # Assuming substation data (substation_id, voltage_level, etc.) is available in the building object
            substation = Substation(
                substation_id=building.building_id,  # Using ID from the building
                voltage_level=building.voltage_rms,  # Assuming 'Voltage RMS' field is there
                max_capacity=1000,  # Set as None, or find the relevant data field
                x_coord=building.position[0],  # Using Position as (x, y)
                y_coord=building.position[1]
            )
            
            substations_dict[building_id] = substation
        
        else:
            # This means the building is a bus
            # Now, the active and reactive power are lists in 'building.active_power' and 'building.reactive_power'
            load_MW = building.active_power  # Keep the active power as a list
            load_MVAR = building.reactive_power  # Keep the reactive power as a list
            
            bus = Bus(
                bus_id=building.building_id,  # Using building's ID
                voltage_level=building.voltage_rms,  # Using 'Voltage RMS'
                load_MW=load_MW,  # Active power as a list
                load_MVAR=load_MVAR,  # Reactive power as a list
                x_coord=building.position[0],  # Using Position (x, y)
                y_coord=building.position[1]
            )
            
            buses_dict[building_id] = bus

    return buses_dict, substations_dict, updated_buildings

@dataclass
class Line:
    line_id: str
    from_bus: int
    to_bus: int
    length: float

def load_lines_csv(file_path,SUBS,LBUS):
    lines_dict = {}
    
    with open(file_path, mode='r', newline='') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        
        for row in csv_reader:
            from_bus = int(row['from bus'])
            to_bus = int(row['to bus'])
            
            if from_bus in SUBS:
                from_x, from_y = SUBS[from_bus].x_coord, SUBS[from_bus].y_coord
            else:
                from_x, from_y = LBUS[from_bus].x_coord, LBUS[from_bus].y_coord
            
            if to_bus in SUBS:
                to_x, to_y = SUBS[to_bus].x_coord, SUBS[to_bus].y_coord
            else:
                to_x, to_y = LBUS[to_bus].x_coord, LBUS[to_bus].y_coord
            
            length = ((to_x - from_x) ** 2 + (to_y - from_y) ** 2) ** 0.5
            
            line = Line(
                line_id=row['Line ID'],
                from_bus=from_bus,
                to_bus=to_bus,
                length=length
            )
            lines_dict[row['Line ID']] = line  # Store in dict by line_id
            
    return lines_dict
