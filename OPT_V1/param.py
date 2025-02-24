#Define the parameters that will be used in the optimization program

from import_file import load_conductors_csv,load_buses_csv, load_substations_csv, load_lines_csv

N_PERIODS = 1


file_path = "conductors_perf.csv"
LINES_OPT = load_conductors_csv(file_path)

subs_file_path = 'substations.csv'
SUBS = load_substations_csv(subs_file_path)

bus_file_path = 'buses.csv'
LBUS = load_buses_csv(bus_file_path,N_PERIODS,len(SUBS))

line_file_path = 'lines.csv'
LINES = load_lines_csv(line_file_path,SUBS,LBUS)

DISCOUNT_RATE = 0.05
DELTA_T = 1
INV_HORIZON_DSO = 30
ALPHA = 365/N_PERIODS*24
UNIT_COST_SUBS = 200 #[k€/MVA]
UNIT_COST_LOSSES = 0.5 #[k€/MWh]
ENERGY_COST = 0.5 #[k€/MWh]
FEED_IN_TARIFF = 0.1 #[€/kWh]
M = 1000
MAX_VOLTAGE = 1.25
MIN_VOLTAGE = 0.75
OMEGA = 1000000
