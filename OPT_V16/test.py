from import_file import *
from optimization import *
from validation import *
from debug import *
from representative_days import *
import dill
from optimization_zero import *

# LOAD DATA--------------------------------------

cities = ["Mycampus", "Abu Dhabi", "Brussels", "Buenos Aires", "Copenhagen", "Los Angeles", "Singapore", "Vancouver", "Montreal", "Tucson", "Miami", "Guayaquil"]
cities = "Brussels"

#Read data from file
LINES_OPT = load_conductors_csv()
LBUS, SUBS, SLACK, irradiation = load_bus(cities)

LINES = get_topologies_by_substation(SUBS, LBUS, SLACK)
plot_topology_basic(LBUS, SUBS, SLACK, LINES)