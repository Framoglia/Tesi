import re
import pandas as pd

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

    html_path = folder_path + "\\" + file_names[0]
    print("Scapring the data from the HTML file")
    building_data = extract_building_data_from_file(html_path)
    print("Data scraped successfully!")


    excel_path = folder_path + "\\" + file_names[1]
    print("Updating the buildings with power data from the Excel file")
    updated_buildings, irradiation = update_buildings_with_power_data(excel_path, building_data, N_PERIODS_MAX, START_N)
    print("Buildings updated successfully!")

    return updated_buildings, irradiation

