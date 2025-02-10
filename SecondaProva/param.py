from import_file import load_conductors_csv, load_bus, load_lines_csv
from generate_lines import generate_lines


N_PERIODS_MAX = 2

file_path = 'conductors_perf.csv'
LINES_OPT = load_conductors_csv(file_path)

LBUS, SUBS, updated_buildings  = load_bus(N_PERIODS_MAX)

keyes = list(LBUS.keys())

N_PERIODS = len(LBUS[keyes[1]].load_MW)

line_file_path = 'lines.csv'


generate_lines(updated_buildings)
print("Lines generated and saved to lines.csv successfully!")
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

for key in LBUS:
    bus = LBUS[key]

    # Check for None and verify length for load_MW
    if bus.load_MW is None:
        print(f"Bus {key} has load_MW as None.")
    elif len(bus.load_MW) != N_PERIODS:
        print(f"Bus {key}: The number of P (load_MW) values is not the same for all the buses.")
        break

    # Check for None and verify length for load_MVAR
    if bus.load_MVAR is None:
        print(f"Bus {key} has load_MVAR as None.")
    elif len(bus.load_MVAR) != N_PERIODS:
        print(f"Bus {key}: The number of Q (load_MVAR) values is not the same for all the buses.")
        break



print("All data loaded successfully!")