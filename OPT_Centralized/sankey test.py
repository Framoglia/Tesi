from checks import *

sankey_cost_check("final_optimal_values.csv")
household_installation_distribution("final_optimal_values.csv")

check_storage("final_optimal_values.csv")