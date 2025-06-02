DISCOUNT_RATE = 0.05
DELTA_T = 1
INV_HORIZON_DSO = 30
UNIT_COST_SUBS_HV = 0.0002             #[k€/VA]
UNIT_COST_SUBS_MV = 0.0003             #[k€/VA]
UNIT_COST_LOSSES = 0.00003             #[k€/kWh]
ENERGY_COST_IMP = 0.00030             #[k€/kWh]
ENERGY_COST_EXP = 0.00007           #[k€/kWh]
M = 1000
MAX_VOLTAGE = 1.05
MIN_VOLTAGE = 0.95
OMEGA = 1000
UNIT_COST_INV = 0.00016                 #[k€/VA]
UNIT_COST_PV = 0.1                      #[k€/m2]
INST_COST_PV = 1                        #[k€/unit]
INST_COST_HV_SUB = 10                   #[k€/unit]
INST_COST_MV_SUB = 100                  #[k€/unit]  
INST_COST_STORAGE = 1.5                 #[k€/unit] 
STORAGE_CAPACITY_COST = 0.44             #[k€/kWh]
STORAGE_POWER_COST = 0.16               #[k€/kW]
STORAGE_EFFICIENCY = 0.9
STORAGE_DAILY_MAX_VARIATION = 1
EV_CHARGE_EFFICIENCY = 0.9
EV_DAILY_MAX_VARIATION = 1
EV_CAPACITY_COST = 0.44             #[k€/kWh]
EV_POWER_COST = 0.16               #[k€/kW]
GAS_COST = 0.00022                        #[k€/kWh]
SURFACE_MULTIPLIER = 1


SCALING = 100 

industrial_growth_demand = 1.2  # Example factor for 15000 voltage level
residential_growth_demand = 1.3  # Example factor for 400 voltage level

# Global threshold mapping (for each district, separate thresholds for EV and HP)
district_thresholds = {
    "1": {"hp": 0.30},
    "2": {"hp": 0.25},
    "3": {"hp": 0.20},
    "4": {"hp": 0.15},
    "5": {"hp": 0.10},
    "6": {"hp": 0.05},
    # Add additional districts as needed
}

# Predefined 24-length arrays for EV and HP loads
hp_daily_load = [0.3] * 24