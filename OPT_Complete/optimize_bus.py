from param import *
from pyomo.environ import *
from utils import *
from pyomo.core import SOSConstraint


def optimize_bus(bus, irradiation, tariffs, N_PERIODS, weights, initial_config):

    ALPHA = 365/N_PERIODS*24
    model = ConcreteModel()

    #Sets that allow to define one variable for each entry

    model.periods = RangeSet(N_PERIODS)
    
    model.C_inv = Var(within=NonNegativeReals)
    model.C_PV = Var(within=NonNegativeReals)
    model.C_storage_capacity = Var(within=NonNegativeReals)
    
    model.PV_inst_cost = Var(within=NonNegativeReals)
    model.storage_inst_cost = Var(within=NonNegativeReals)
    model.C_electricity = Var(model.periods, within=Reals)

    model.total_C_electricity = Expression(expr=sum(model.C_electricity[p] * get_weights(p, weights) for p in model.periods)) #Total cost of electricity

    model.P_load = Param(model.periods, mutable=True)
    model.Q_load = Param(model.periods, mutable=True)

    model.P_pv = Var(model.periods, within=NonNegativeReals)
    model.P_inv = Var(model.periods, within=NonNegativeReals)
    model.Q_inv = Var(model.periods, within=NonNegativeReals)
    model.S_inv = Var(within=NonNegativeReals)
    model.PV_surf = Var(within=NonNegativeReals)
    model.pi = Var(within=Binary)

    model.P_bus = Var(model.periods, within=Reals) #Power injected in the bus
    model.Q_bus = Var(model.periods, within=Reals)

    model.Irr = Param(model.periods, mutable=True)  

    model.storage_option = Var(within=Binary)
    model.storage_capacity = Var(within=NonNegativeReals)
    model.P_storage_charge = Var(model.periods, within=NonNegativeReals) 
    model.P_storage_discharge = Var(model.periods, within=NonNegativeReals)
    model.storage_energy = Var(model.periods, within=NonNegativeReals)

    model.initial_pi = Param(mutable=True)
    model.initial_capacity_inv = Param(mutable=True)
    model.initial_PV_surf = Param(mutable=True)
    model.initial_storage_option = Param(mutable=True)
    model.initial_storage_capacity = Param(mutable=True)
        
    if 'pi' not in initial_config:
        
        model.initial_capacity_inv = 0
        model.initial_PV_surf = 0
        model.initial_pi = 0
        model.initial_storage_option = 0
        model.initial_storage_capacity = 0

    else:
        model.initial_capacity_inv = initial_config.S_inv.value
        model.initial_PV_surf = initial_config.PV_surf.value
        model.initial_pi = initial_config.pi.value
        model.initial_storage_option = initial_config.storage_option.value
        model.initial_storage_capacity = initial_config.storage_capacity.value
        model.initial_storage_power = initial_config.storage_power.value



    for p in model.periods:
        if 0 <= p-1 < len(bus.load_kVAR):
            model.P_load[p] = bus.load_kW[p-1] * 10**3 / BASE_POWER #1000 VA
            model.Q_load[p] = bus.load_kVAR[p-1] * 10**3 / BASE_POWER

    for p in model.periods:
                model.Irr[p] = irradiation[p-1]


    #Constraints
 
    def energy_imp_cost_rule(m,p): ##Why should i pay P bus and not S_HV  it would already count losses??
        return m.C_electricity[p] >= m.P_bus[p] * BASE_POWER / 1000 * ENERGY_COST_IMP * DELTA_T
    
    def energy_exp_cost_rule(m,p):
        return m.C_electricity[p] >= m.P_bus[p] * BASE_POWER / 1000 * ENERGY_COST_EXP * DELTA_T
    
    def bus_active_power_balance_rule(m,p):
        return m.P_bus[p] == m.P_load[p] - m.P_inv[p]
    
    def bus_reactive_power_balance_rule(m,p):
        return m.Q_bus[p] == m.Q_load[p] - m.Q_inv[p] 
    
    def pv_production_rule(m,p):
        return m.P_pv[p] * BASE_POWER / 1000 <= m.PV_surf * m.Irr[p] * 0.2 / 1000
    
    def inverter_limit_rule(m,p):
        constraints = []
        n=16
        coefficients ,scale_factor = obtain_coef(n)
        
        for a, c in coefficients:
            constraints.append(m.S_inv / scale_factor >= a * m.P_inv[p] + c * m.Q_inv[p])
        
        return constraints
    
    def inverter_cost_rule(m):                                                              
        return m.C_inv == (m.S_inv - m.initial_capacity_inv) * BASE_POWER * UNIT_COST_INV
    
    def PV_cost_rule(m):
        return m.C_PV == (m.PV_surf - m.initial_PV_surf) * UNIT_COST_PV
    
    def PV_surf_limit(m):
        return m.PV_surf <= bus.surface * SURFACE_MULTIPLIER
    
    def PV_investment_rule(m):
        return m.pi * 1000 >= m.PV_surf

    def PV_inv_cost_rule(m):
        return m.PV_inst_cost == (m.pi - m.initial_pi) * INST_COST_PV 
    
    def storage_inst_cost_rule(m):
        return m.storage_inst_cost == (m.storage_option - m.initial_storage_option) * INST_COST_STORAGE
    
    def PV_increasing_rule(m):
        return m.PV_surf >= m.initial_PV_surf
    
    def inv_increasing_rule(m):
        return m.S_inv >= m.initial_capacity_inv

    def storage_capacity_rule(m):
        return m.storage_option >= m.storage_capacity
    
    def storage_energy_rule(m,p):
        if (p-1)%24 != 0 and (p-1)%24 != 1:
            return m.storage_energy[p] == m.storage_energy[p-1] + (m.P_storage_charge[p] * STORAGE_EFFICIENCY - m.P_storage_discharge[p] / STORAGE_EFFICIENCY) * DELTA_T 
        elif (p-1)%24 == 1:
            return m.storage_energy[p] == m.storage_energy[p-1] + ((m.P_storage_charge[p] + m.P_storage_charge[p-1]) * EV_CHARGE_EFFICIENCY - (m.P_storage_discharge[p] + m.P_storage_discharge[p-1]) / EV_CHARGE_EFFICIENCY) * DELTA_T
        else:
            return m.storage_energy[p+23] >= m.storage_energy[p] * STORAGE_DAILY_MAX_VARIATION
        
    def storage_soc_limit_rule(m,p):
        return m.storage_energy[p] <= m.storage_capacity
    
    def storage_capacity_cost_rule(m):
        return m.C_storage_capacity == (m.storage_capacity - m.initial_storage_capacity)  * STORAGE_CAPACITY_COST * BASE_POWER / 1000
    
    def DC_balance_rule(m,p):
        return m.P_pv[p] + m.P_storage_discharge[p] - m.P_storage_charge[p] == m.P_inv[p]


    model.PV_incr_cstr = Constraint(rule=PV_increasing_rule)
    model.inv_incr_cstr = Constraint(rule=inv_increasing_rule)
    
    model.bus_active_power_balance_cstr = Constraint(model.periods, rule=bus_active_power_balance_rule)
    model.bus_reactive_power_balance_cstr = Constraint(model.periods, rule=bus_reactive_power_balance_rule)

    model.pv_production_cstr = Constraint(model.periods, rule=pv_production_rule)
    model.inverter_cost_cstr = Constraint(rule=inverter_cost_rule)
    model.PV_cost_cstr = Constraint(rule=PV_cost_rule)
    model.PV_surf_limit_cstr = Constraint(rule=PV_surf_limit)

    model.inverter_limit_cstr = ConstraintList()
    for p in model.periods:
        for constr in inverter_limit_rule(model, p):
            model.inverter_limit_cstr.add(constr)

    model.DC_balance_cstr = Constraint(model.periods, rule=DC_balance_rule)

    model.storage_capacity_cstr = Constraint(rule=storage_capacity_rule)
    model.storage_capacity_cost_cstr = Constraint(rule=storage_capacity_cost_rule)
    model.storage_inst_cost_cstr = Constraint(rule=storage_inst_cost_rule)

    model.storage_energy_cstr = Constraint(model.periods, rule=storage_energy_rule)
    model.storage_soc_limit_cstr = Constraint(model.periods, rule=storage_soc_limit_rule)


    model.energy_imp_cost_cstr = Constraint(model.periods, rule=energy_imp_cost_rule)
    model.energy_exp_cost_cstr = Constraint(model.periods, rule=energy_exp_cost_rule)


    model.pv_inst_cstr = Constraint(rule=PV_investment_rule)
    model.investment_cost_cstr = ConstraintList()
    model.investment_cost_cstr.add(PV_inv_cost_rule(model))



    def objective_rule(m):
        return 1/INV_HORIZON_DSO * (m.C_inv + m.C_PV + m.PV_inst_cost + m.storage_inst_cost + m.C_storage_capacity) + (m.total_C_electricity)
    
    model.total_C = Expression(expr=1/INV_HORIZON_DSO * (model.C_inv + model.C_PV + model.PV_inst_cost + model.storage_inst_cost + model.C_storage_capacity) + (model.total_C_electricity))


    model.objective_rule = Objective(rule=objective_rule, sense=minimize)

    # Solve the model
    
    solver = SolverFactory('gurobi')

    results = solver.solve(model)

    load_kw = [model.P_bus[p].value * 1000 for p in model.periods]
    load_kvar = [model.Q_bus[p].value * 1000 for p in model.periods]
    inv_info = {
        
        'PV_surf': model.PV_surf.value,
        'PV_fraction': model.PV_surf.value / (bus.surface * SURFACE_MULTIPLIER),
        'S_inv': round(model.S_inv.value * 1000 , 2),  # Convert to kVA
        'Inv_size_factor' : round((model.S_inv.value / (model.PV_surf.value * 0.2 / 1000)) , 2), 
        'storage_capacity': model.storage_capacity.value * 1000,  # Convert to kWh
        'yearly_cost': round(value(model.total_C, 2))
    }
    return load_kw, load_kvar, inv_info