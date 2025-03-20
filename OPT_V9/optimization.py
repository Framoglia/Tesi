from param import *
from pyomo.environ import *
from utils import *


def optimize_log(LBUS, SUBS, SLACK, LINES, LINES_OPT, N_PERIODS, irradiation, setting = [2,15,2,16]):
    lin_type, NPWB, limits, n_segm = setting
    DATA = LBUS,SUBS, SLACK, LINES,LINES_OPT,N_PERIODS

    ALPHA = 365/N_PERIODS*24
    model = ConcreteModel()

    #Sets that allow to define one variable for each entry

    model.periods = RangeSet(N_PERIODS)
    model.conductors = Set(initialize=LINES_OPT.keys()) 
    model.lines = Set(initialize=LINES.keys())  
    model.buses = Set(initialize=LBUS.keys())
    model.subs_hv = Set(initialize=SLACK.keys())
    model.subs_mv = Set(initialize=SUBS.keys())

    model.B = model.buses | model.subs_mv
    
    #Variables

    model.C_cond = Var(within=NonNegativeReals)  
    model.C_subs = Var(within=NonNegativeReals)  
    model.C_losses = Var(model.periods, within=NonNegativeReals)  
    model.C_inv = Var(within=NonNegativeReals)
    model.C_PV = Var(within=NonNegativeReals)
    model.C_electricity = Var(model.periods, within=Reals)
    model.subs_hv_inst_cost = Var(within=NonNegativeReals)
    model.subs_mv_inst_cost = Var(within=NonNegativeReals)
    model.PV_inst_cost = Var(within=NonNegativeReals)

    model.line_opt = Var(model.lines, model.conductors, within=Binary)  # Conductor chosen when line is active 
    model.line_act_plus = Var(model.lines, within=Binary)                    # Is the line activated ?
    model.line_act_minus = Var(model.lines, within=Binary)  

    model.subs_hv_capacity = Var(model.subs_hv, within=NonNegativeReals)
    model.subs_hv_S = Var(model.periods, model.subs_hv, within=NonNegativeReals)
    model.subs_hv_P = Var(model.periods, model.subs_hv, within=Reals)
    model.subs_hv_Q = Var(model.periods, model.subs_hv, within=Reals)
    model.beta = Var(model.subs_hv, within=Binary)

    model.subs_mv_capacity = Var(model.subs_mv, within=NonNegativeReals)
    model.subs_mv_S = Var(model.periods, model.subs_mv, within=NonNegativeReals)
    model.subs_mv_P = Var(model.periods, model.subs_mv, within=Reals)
    model.subs_mv_Q = Var(model.periods, model.subs_mv, within=Reals)
    model.gamma = Var(model.subs_mv, within=Binary)

    model.current_squared_k = Var(model.periods, model.lines, model.conductors, within=NonNegativeReals)
    model.current_squared = Var(model.periods, model.lines, within=NonNegativeReals)
    model.current_slack = Var(model.periods, model.lines, model.conductors, within=NonNegativeReals)
    model.phi = Var(model.periods, within=NonNegativeReals)
    model.losses = Var(model.periods, model.lines, within=NonNegativeReals)

    model.active_power_k = Var( model.periods,model.lines, model.conductors, within=Reals)
    model.active_power = Var(model.periods, model.lines, within=Reals)

    model.reactive_power_k = Var(model.periods, model.lines, model.conductors, within=Reals)
    model.reactive_power = Var(model.periods, model.lines, within=Reals)

    model.voltage_squared = Var(model.periods, model.subs_hv | model.B, within=NonNegativeReals)

    model.P_load = Param(model.periods, model.buses, mutable=True)
    model.Q_load = Param(model.periods, model.buses, mutable=True)

    model.P_sun = Var(model.periods, model.buses, within=NonNegativeReals)
    model.Q_sun = Var(model.periods, model.buses, within=NegativeReals)

    model.S_sun = Var(model.periods, model.buses, within=NonNegativeReals)
    model.S_inv = Var(model.buses, within=NonNegativeReals)
    model.PV_surf = Var(model.buses, within=NonNegativeReals)
    model.pi = Var(model.buses, within=Binary)

    model.P_bus = Var(model.periods, model.buses, within=Reals) #Power injected in the bus
    model.Q_bus = Var(model.periods, model.buses, within=Reals)

    model.Irr = Param(model.periods, mutable=True)  

    # Model parameters representing initial investment status:

    model.initial_line_act = Param(model.lines, mutable=True)
    model.initial_line_opt = Param(model.lines, model.conductors, mutable=True)
    model.initial_beta = Param(model.subs_hv, mutable=True)
    model.initial_gamma = Param(model.subs_mv, mutable=True)
    model.initial_pi = Param(model.buses, mutable=True)
    model.initial_capacity_hv = Param(model.subs_hv, mutable=True)
    model.initial_capacity_mv = Param(model.subs_mv, mutable=True)
    model.initial_capacity_inv = Param(model.buses, mutable=True)
    model.initial_PV_surf = Param(model.buses, mutable=True)

    for l in model.lines:
        model.initial_line_act[l] = 0
        for c in model.conductors:
            model.initial_line_opt[l,c] = 0
    for s in model.subs_hv:
        model.initial_beta[s] = 0
        model.initial_capacity_hv[s] = 0
    for s in model.subs_mv:
        model.initial_gamma[s] = 0
        model.initial_capacity_mv[s] = 0
    for b in model.buses:
        model.initial_capacity_inv[b] = 0
        model.initial_PV_surf[b] = 0
        model.initial_pi[b] = 0

    if lin_type != 0:
        model.NPWB = RangeSet(NPWB)
        model.active_power_plus = Var(model.periods, model.lines, within=NonNegativeReals)
        model.reactive_power_plus = Var(model.periods, model.lines, within=NonNegativeReals)
        model.active_power_minus = Var(model.periods, model.lines, within=NonNegativeReals)
        model.reactive_power_minus = Var(model.periods, model.lines, within=NonNegativeReals)

        model.active_power_discr = Var(model.periods, model.lines, model.NPWB, within=NonNegativeReals)
        model.reactive_power_discr = Var(model.periods, model.lines, model.NPWB, within=NonNegativeReals)

        model.LPWB = Param(model.lines, model.NPWB, mutable=True)
        model.SPWB = Param(model.lines, model.NPWB, mutable=True)
    
        for l in model.lines:
            max_power = MAX_VOLTAGE * max((LINES_OPT[c].imax_kA*1000) for c in model.conductors) / fetch_base_i_from_line(DATA, l)

            X1 = 0  # Start from zero
            for block in model.NPWB:
                if lin_type == 1:
                    LPWB_block = max_power/NPWB
                else:
                    LPWB_block = log_interval_length(max_power, NPWB, block)      # Get the length of the current interval
                X2 = X1 + LPWB_block                                            # Compute the boundary points
                model.LPWB[l, block] = LPWB_block
                model.SPWB[l, block] = X1 + X2                                  # Compute the true slope of x^2 using boundary points          
                X1 = X2                                                         # Move to the next interval

                #print(f"LPWB[{l},{block}] = {model.LPWB[l, block].value}")
                #print(f"SPWB[{l},{block}] = {model.SPWB[l, block].value}")

    for p in model.periods:
        for b in model.buses:  
            
            if 0 <= p-1 < len(LBUS[b].load_kVAR):
                model.P_load[p, b] = LBUS[b].load_kW[p-1] * 10**3 / BASE_POWER #1000 VA
                model.Q_load[p, b] = LBUS[b].load_kVAR[p-1] * 10**3 / BASE_POWER

                #print(model.P_load[p, b].value, model.Q_load[p, b].value)

    for p in model.periods:
                model.Irr[p] = irradiation[p-1]


    #Constraints

    def conductors_cost(m):
        return m.C_cond == sum( (m.line_opt[l, c] - m.initial_line_opt[l,c] )* LINES_OPT[c].cost_keur_per_km * LINES[l].length  / 100 for l in m.lines for c in m.conductors) * 1000 #eur

    def substation_cost(m):
        return m.C_subs == sum(UNIT_COST_SUBS_HV * (m.subs_hv_capacity[s]-m.initial_capacity_hv[s]) * BASE_POWER for s in m.subs_hv) + sum(UNIT_COST_SUBS_MV * (m.subs_mv_capacity[s]-m.initial_capacity_mv[s]) * BASE_POWER for s in m.subs_mv)

    def loss_cost(m,p):
        return m.C_losses[p] == sum(LINES_OPT[c].r_per_km / fetch_base_z_from_line(DATA, l) * LINES[l].length  / 100 * m.current_squared_k[p,l,c] for l in m.lines for c in m.conductors) * BASE_POWER / 1000 * UNIT_COST_LOSSES * DELTA_T

    def budget_balance(m):
        return (1+DISCOUNT_RATE)**INV_HORIZON_DSO * (m.C_cond + m.C_subs) + INV_HORIZON_DSO * ALPHA * sum(m.C_losses[p] for p in m.periods) <= INV_HORIZON_DSO * ALPHA * sum(m.p_imp[p,b] for b in m.buses for p in m.periods) * BASE_POWER / 1000 * ENERGY_COST_IMP * DELTA_T

    def active_power_rule(m,p,l):
        return m.active_power[p,l] == sum(m.active_power_k[p,l,c] for c in m.conductors)

    def reactive_power_rule(m,p,l):
        return m.reactive_power[p,l] == sum(m.reactive_power_k[p,l,c] for c in m.conductors)

    def curent_squared_rule(m,p,l):
        return m.current_squared[p,l] == sum(m.current_squared_k[p,l,c] for c in m.conductors)

    def active_power_subs_hv_rule(m,p,s):    #Ha senso mettere per ogni linea???
        return m.subs_hv_P[p,s] == -(sum(m.active_power_k[p,l,c] - m.current_squared_k[p,l,c] * LINES_OPT[c].r_per_km / fetch_base_z_from_line(DATA, l) * LINES[l].length  / 100 for c in m.conductors for l in m.lines if LINES[l].to_bus==s) - sum(m.active_power_k[p,l,c] for c in m.conductors for l in m.lines if LINES[l].from_bus==s))

    def reactive_power_subs_hv_rule(m,p,s):
        return m.subs_hv_Q[p,s] == -(sum(m.reactive_power_k[p,l,c] - m.current_squared_k[p,l,c] * LINES_OPT[c].xl_per_km / fetch_base_z_from_line(DATA, l) * LINES[l].length  / 100 for c in m.conductors for l in m.lines if LINES[l].to_bus==s) - sum(m.reactive_power_k[p,l,c] for c in m.conductors for l in m.lines if LINES[l].from_bus==s))

    def apparent_power_subs_hv(m,p,s):
        return m.subs_hv_S[p,s]**2 >= m.subs_hv_P[p,s]**2 + m.subs_hv_Q[p,s]**2

    def active_power_subs_mv_rule(m,p,s):    
        return 0 == -(sum(m.active_power_k[p,l,c] - m.current_squared_k[p,l,c] * LINES_OPT[c].r_per_km / fetch_base_z_from_line(DATA, l) * LINES[l].length  / 100 for c in m.conductors for l in m.lines if LINES[l].to_bus==s) - sum(m.active_power_k[p,l,c] for c in m.conductors for l in m.lines if LINES[l].from_bus==s))

    def reactive_power_subs_mv_rule(m,p,s):
        return 0 == -(sum(m.reactive_power_k[p,l,c] - m.current_squared_k[p,l,c] * LINES_OPT[c].xl_per_km / fetch_base_z_from_line(DATA, l) * LINES[l].length  / 100 for c in m.conductors for l in m.lines if LINES[l].to_bus==s) - sum(m.reactive_power_k[p,l,c] for c in m.conductors for l in m.lines if LINES[l].from_bus==s))

    def active_power_lbus_rule(m,p,b):
        return m.P_bus[p,b]  == (sum(m.active_power_k[p,l,c] - m.current_squared_k[p,l,c] * LINES_OPT[c].r_per_km / fetch_base_z_from_line(DATA, l) * LINES[l].length  / 100 for c in m.conductors for l in m.lines if LINES[l].to_bus==b) - sum(m.active_power_k[p,l,c] for c in m.conductors for l in m.lines if LINES[l].from_bus==b))

    def reactive_power_lbus_rule(m,p,b):
        return m.Q_bus[p,b]  == (sum(m.reactive_power_k[p,l,c] - m.current_squared_k[p,l,c] * LINES_OPT[c].xl_per_km / fetch_base_z_from_line(DATA, l) * LINES[l].length  / 100 for c in m.conductors for l in m.lines if LINES[l].to_bus==b) - sum(m.reactive_power_k[p,l,c] for c in m.conductors for l in m.lines if LINES[l].from_bus==b))

    def voltage_rule_1(m,p,l):
        i = LINES[l].from_bus
        j = LINES[l].to_bus

        base_z = fetch_base_z_from_line(DATA, l)
        length = LINES[l].length
        scaling_factor = length / base_z / 100

        return (m.voltage_squared[p,j] - m.voltage_squared[p,i]) / scaling_factor  <= sum(-2 * (LINES_OPT[c].r_per_km * m.active_power_k[p,l,c] + LINES_OPT[c].xl_per_km * m.reactive_power_k[p,l,c]) + m.current_squared_k[p,l,c] * ((LINES_OPT[c].r_per_km **2 + LINES_OPT[c].xl_per_km **2) * scaling_factor) for c in m.conductors) + M * (1-m.line_act_plus[l]-m.line_act_minus[l])

    def voltage_rule_2(m,p,l):
        i = LINES[l].from_bus
        j = LINES[l].to_bus

        base_z = fetch_base_z_from_line(DATA, l)
        length = LINES[l].length
        scaling_factor = length / base_z / 100

        return (m.voltage_squared[p,j] - m.voltage_squared[p,i]) / scaling_factor  >= sum(-2 * (LINES_OPT[c].r_per_km * m.active_power_k[p,l,c] + LINES_OPT[c].xl_per_km * m.reactive_power_k[p,l,c]) + m.current_squared_k[p,l,c] * ((LINES_OPT[c].r_per_km **2 + LINES_OPT[c].xl_per_km **2) * scaling_factor) for c in m.conductors) - M * (1-m.line_act_plus[l]-m.line_act_minus[l])

    def complex_power_rule(m,p,l):
        return  m.current_squared[p,l] >= sum(m.SPWB[l,db] * (m.active_power_discr[p,l,db] + m.reactive_power_discr[p,l,db]) for db in m.NPWB)
    
    def conic_complex_power_rule(m,p,l):
        return  m.voltage_squared[p,LINES[l].from_bus] * m.current_squared[p,l] >= m.active_power[p,l]**2 + m.reactive_power[p,l]**2

    def subs_capacity_rule(m,p,s):
        return m.subs_hv_S[p,s] <= m.subs_hv_capacity[s]

    def max_capacity_rule(m,s):
        return m.subs_hv_capacity[s] <= m.beta[s] * SLACK[s].max_capacity / BASE_POWER

    def subs_voltage_rule_1(m,p,s):
        return m.voltage_squared[p,s] - 1 <= (MAX_VOLTAGE**2 - 1) * (1-m.beta[s])

    def subs_voltage_rule_2(m,p,s):
        return m.voltage_squared[p,s] - 1 >= (MIN_VOLTAGE**2 - 1) * (1-m.beta[s])
    
    def active_power_subs_mv_lv_rule(m,p,s):    #Ha senso mettere per ogni linea???
        return m.subs_mv_P[p,s] == -(sum(m.active_power_k[p,l,c] - m.current_squared_k[p,l,c] * LINES_OPT[c].r_per_km / fetch_base_z_from_line(DATA, l) * LINES[l].length  / 100 for c in m.conductors for l in m.lines if LINES[l].to_bus==s and is_line_from_LV_load(DATA, l)) - sum(m.active_power_k[p,l,c] for c in m.conductors for l in m.lines if LINES[l].from_bus==s and is_line_to_LV_load(DATA,l)))

    def reactive_power_subs_mv_lv_rule(m,p,s):
        return m.subs_mv_Q[p,s] == -(sum(m.reactive_power_k[p,l,c] - m.current_squared_k[p,l,c] * LINES_OPT[c].xl_per_km / fetch_base_z_from_line(DATA, l) * LINES[l].length  / 100 for c in m.conductors for l in m.lines if LINES[l].to_bus==s and is_line_from_LV_load(DATA, l)) - sum(m.reactive_power_k[p,l,c] for c in m.conductors for l in m.lines if LINES[l].from_bus==s and is_line_to_LV_load(DATA, l)))

    def apparent_power_subs_mv(m,p,s):
        return m.subs_mv_S[p,s]**2 >= m.subs_mv_P[p,s]**2 + m.subs_mv_Q[p,s]**2
    
    def subs_mv_capacity_rule(m,p,s):
        return m.subs_mv_S[p,s] <= m.subs_mv_capacity[s]

    def max_mv_capacity_rule(m,s):
        return m.subs_mv_capacity[s] <= m.gamma[s] * SUBS[s].max_capacity / BASE_POWER

    def lbus_voltage_rule_1(m,p,l,c):
        return m.active_power_k[p,l,c] <= m.line_opt[l,c] * (LINES_OPT[c].imax_kA*1000) / fetch_base_i_from_line(DATA, l) * MAX_VOLTAGE

    def lbus_voltage_rule_2(m,p,l,c):
        return m.active_power_k[p,l,c] >= -m.line_opt[l,c] * (LINES_OPT[c].imax_kA*1000) / fetch_base_i_from_line(DATA, l) * MAX_VOLTAGE

    def lbus_voltage_rule_3(m,p,l,c):
        return m.reactive_power_k[p,l,c] <=  m.line_opt[l,c] * (LINES_OPT[c].imax_kA*1000) / fetch_base_i_from_line(DATA, l) * MAX_VOLTAGE

    def lbus_voltage_rule_4(m,p,l,c):
        return m.reactive_power_k[p,l,c] >= -m.line_opt[l,c] * (LINES_OPT[c].imax_kA*1000) / fetch_base_i_from_line(DATA, l) * MAX_VOLTAGE

    def current_slack_rule_2(m,p,l,c):
        return m.current_squared_k[p,l,c] - m.current_slack[p,l,c] <= (LINES_OPT[c].imax_kA*1000)**2 / fetch_base_i_from_line(DATA, l)**2 * (m.line_opt[l,c])

    def line_activation_rule(m,l):
        return m.line_act_plus[l] + m.line_act_minus[l] == sum(m.line_opt[l,c] for c in m.conductors)

    def topology_rule(m):
        return sum(m.line_act_plus[l] + m.line_act_minus[l] for l in m.lines) == len(LBUS.keys()) + sum(m.gamma[s] for s in m.subs_mv)
    
    def total_overloads_rule(m,p):
        return sum(m.current_slack[p,l,c] for l in m.lines for c in m.conductors) == m.phi[p]
    
    def one_direction_rule(m,l):
        return(m.line_act_plus[l] + m.line_act_minus[l]<=1)

    def topology_rule_2(m,s):
        return sum(m.line_act_minus[l] for l in m.lines if LINES[l].from_bus==s) + sum(m.line_act_plus[l] for l in m.lines if LINES[l].to_bus==s) >= 1
    
    def active_power_scomposition_rule(m,p,l):
        return m.active_power[p,l] == m.active_power_plus[p,l] - m.active_power_minus[p,l]
    
    def reactive_power_scomposition_rule(m,p,l):
        return m.reactive_power[p,l] == m.reactive_power_plus[p,l] - m.reactive_power_minus[p,l]
    
    def active_power_discr_rule(m,p,l):
        return m.active_power_plus[p,l] + m.active_power_minus[p,l] == sum(m.active_power_discr[p,l,d] for d in m.NPWB)
    
    def reactive_power_discr_rule(m,p,l):
        return m.reactive_power_plus[p,l] + m.reactive_power_minus[p,l] == sum(m.reactive_power_discr[p,l,d] for d in m.NPWB)
    
    def active_power_discr_limit_rule(m,p,l,d):
        return m.active_power_discr[p,l,d] <= m.LPWB[l,d]
    
    def reactive_power_discr_limit_rule(m,p,l,d):
        return m.reactive_power_discr[p,l,d] <= m.LPWB[l,d]
    
    def voltage_lim_1_rule(m,p,b):
        return m.voltage_squared[p,b] >= MIN_VOLTAGE**2

    def voltage_lim_2_rule(m,p,b):
        return m.voltage_squared[p,b] <= MAX_VOLTAGE**2
    
    def apparent_power_subs_hv_rule(m, p, s):
        constraints = []
        n=n_segm
        coefficients ,scale_factor = obtain_coef(n)

        if limits == 1:
            mult = scale_factor
        else: 
            mult = 1
        
        for a, b in coefficients:
            constraints.append(m.subs_hv_S[p, s] / mult >= a * m.subs_hv_P[p, s] + b * m.subs_hv_Q[p, s])
        
        return constraints
    
    def apparent_power_subs_mv_rule(m, p, s):
        constraints = []
        n=n_segm
        coefficients ,scale_factor = obtain_coef(n)

        if limits == 1:
            mult = scale_factor
        else: 
            mult = 1
        
        for a, b in coefficients:
            constraints.append(m.subs_mv_S[p, s] / mult >= a * m.subs_mv_P[p, s] + b * m.subs_mv_Q[p, s])
        
        return constraints

    def losses_rule(m,p,l):
        return m.losses[p,l] * 100 == sum(m.current_squared_k[p,l,c] * LINES_OPT[c].r_per_km / fetch_base_z_from_line(DATA, l) * LINES[l].length  for c in m.conductors)
    
    def bus_active_power_balance_rule(m,p,b):
        return m.P_bus[p,b] == m.P_load[p,b] - m.P_sun[p,b]
    
    def energy_imp_cost_rule(m,p):
        return m.C_electricity[p] >= sum(m.P_bus[p,b] for b in m.buses) * BASE_POWER / 1000 * ENERGY_COST_IMP * DELTA_T
    
    def energy_exp_cost_rule(m,p):
        return m.C_electricity[p] >= sum(m.P_bus[p,b] for b in m.buses) * BASE_POWER / 1000 * ENERGY_COST_EXP * DELTA_T
    
    def bus_reactive_power_balance_rule(m,p,b):
        return m.Q_bus[p,b] == m.Q_load[p,b] - m.Q_sun[p,b]
    
    def sun_power_rule_1(m,p,b):                                                  #Questa da rivedere con i veri limiti??
        return m.S_sun[p,b] == m.P_sun[p,b]
    
    def sun_power_rule_2(m,p,b):
        return m.P_sun[p,b] >= - m.Q_sun[p,b]
    
    def sun_power_rule_3(m,p,b):
        return m.P_sun[p,b] >= m.Q_sun[p,b]
    
    def inv_limit_rule(m,p,b):
        return m.S_inv[b] >= m.S_sun[p,b]
    
    def pv_production_rule(m,p,b):
        return m.S_sun[p,b] * BASE_POWER <= m.PV_surf[b] * m.Irr[p] * 0.2
    
    def inverter_cost_rule(m):                                                              #TODO: aggiungere i costi all' objective rule
        return m.C_inv == sum((m.S_inv[b] - m.initial_capacity_inv[b]) * BASE_POWER * UNIT_COST_INV for b in m.buses)
    
    def PV_cost_rule(m):
        return m.C_PV == sum((m.PV_surf[b] - m.initial_PV_surf[b]) * UNIT_COST_PV for b in m.buses)
    
    def PV_surf_limit(m,b):
        return m.PV_surf[b] <= LBUS[b].surface
    
    def PV_investment_rule(m,b):
        return m.pi[b] * 1000 >= m.PV_surf[b]

    def PV_inv_cost_rule(m):
        return model.PV_inst_cost == sum((m.pi[b] - m.initial_pi[b]) * INST_COST_PV for b in m.buses)
    
    def hv_subs_inv_cost_rule(m):
        return model.subs_hv_inst_cost == sum((m.beta[s] - m.initial_beta[s]) * INST_COST_HV_SUB for s in model.subs_hv)
    
    def mv_subs_inv_cost_rule(m):
        return model.subs_mv_inst_cost == sum((m.gamma[s] - m.initial_gamma[s]) * INST_COST_MV_SUB for s in model.subs_mv)
    
    def PV_increasing_rule(m,b):
        return model.PV_surf[b] >= model.initial_PV_surf[b]
    
    def inv_increasing_rule(m,b):
        return model.S_inv[b] >= model.initial_capacity_inv[b]
    
    def hv_increasing_rule(m,s):
        return model.subs_hv_capacity[s] >= model.initial_capacity_hv[s]
    
    def mv_increasing_rule(m,s):
        return model.subs_mv_capacity[s] >= model.initial_capacity_mv[s]
    
    model.PV_incr_cstr = Constraint(model.buses, rule=PV_increasing_rule)
    model.inv_incr_cstr = Constraint(model.buses, rule=inv_increasing_rule)
    model.hv_incr_cstr = Constraint(model.subs_hv, rule=hv_increasing_rule)
    model.mv_incr_cstr = Constraint(model.subs_mv, rule=mv_increasing_rule)

    model.conductors_cost = Constraint(rule=conductors_cost)
    model.substation_cost = Constraint(rule=substation_cost)
    model.loss_cost = Constraint(model.periods, rule=loss_cost)
    #model.budget_balance = Constraint(rule=budget_balance)
    
    model.active_power_cstr = Constraint(model.periods, model.lines, rule=active_power_rule)
    model.reactive_power_cstr = Constraint(model.periods, model.lines, rule=reactive_power_rule)
    model.curent_squared_cstr = Constraint(model.periods, model.lines, rule=curent_squared_rule)
    
    model.active_power_subs_hv_cstr = Constraint(model.periods, model.subs_hv, rule=active_power_subs_hv_rule)
    model.reactive_power_subs_hv_cstr = Constraint(model.periods, model.subs_hv, rule=reactive_power_subs_hv_rule)

    model.active_power_subs_mv_cstr = Constraint(model.periods, model.subs_mv, rule=active_power_subs_mv_rule)
    model.reactive_power_subs_mv_cstr = Constraint(model.periods, model.subs_mv, rule=reactive_power_subs_mv_rule)

    model.active_power_subs_mv_lv_cstr = Constraint(model.periods, model.subs_mv, rule=active_power_subs_mv_lv_rule)
    model.reactive_power_subs_m_lvv_cstr = Constraint(model.periods, model.subs_mv, rule=reactive_power_subs_mv_lv_rule)
    
    model.active_power_lbus_cstr = Constraint(model.periods, model.buses, rule=active_power_lbus_rule)
    model.reactive_power_lbus_cstr = Constraint(model.periods, model.buses, rule=reactive_power_lbus_rule)
    
    model.voltage_cstr_1 = Constraint(model.periods, model.lines, rule=voltage_rule_1)
    model.voltage_cstr_2 = Constraint(model.periods, model.lines, rule=voltage_rule_2)

    model.subs_capacity_cstr = Constraint(model.periods, model.subs_hv, rule=subs_capacity_rule)
    model.max_capacity_cstr = Constraint(model.subs_hv, rule=max_capacity_rule)
    model.subs_voltage_cstr_1 = Constraint(model.periods, model.subs_hv, rule=subs_voltage_rule_1)
    model.subs_voltage_cstr_2 = Constraint(model.periods, model.subs_hv, rule=subs_voltage_rule_2)

    if limits == 0:
        model.apparent_power_subs_mv_cstr = Constraint(model.periods, model.subs_mv, rule=apparent_power_subs_mv)

        model.apparent_power_subs_cstr = Constraint(model.periods, model.subs_hv, rule=apparent_power_subs_hv)

    else:
        model.apparent_power_subs_mv_cstr = ConstraintList()
        for p in model.periods:
            for s in model.subs_mv:
                for constr in apparent_power_subs_mv_rule(model, p, s):
                    model.apparent_power_subs_mv_cstr.add(constr)

        model.apparent_power_subs_hv_cstr = ConstraintList()
        for p in model.periods:
            for s in model.subs_hv:
                for constr in apparent_power_subs_hv_rule(model, p, s):
                    model.apparent_power_subs_hv_cstr.add(constr)

    model.subs_mv_capacity_cstr = Constraint(model.periods, model.subs_mv, rule=subs_mv_capacity_rule)
    model.max_mv_capacity_cstr = Constraint(model.subs_mv, rule=max_mv_capacity_rule)
    
    model.lbus_voltage_cstr_1 = Constraint(model.periods, model.lines, model.conductors, rule=lbus_voltage_rule_1)
    model.lbus_voltage_cstr_2 = Constraint(model.periods, model.lines, model.conductors, rule=lbus_voltage_rule_2)
    
    model.lbus_voltage_cstr_3 = Constraint(model.periods, model.lines, model.conductors, rule=lbus_voltage_rule_3)
    model.lbus_voltage_cstr_4 = Constraint(model.periods, model.lines, model.conductors, rule=lbus_voltage_rule_4)
    
    model.current_slack_cstr_2 = Constraint(model.periods, model.lines, model.conductors, rule=current_slack_rule_2)
    
    model.line_activation_cstr = Constraint(model.lines, rule=line_activation_rule)
    
    model.topology_cstr = Constraint(rule=topology_rule)
    model.total_overloads_cstr = Constraint(model.periods, rule=total_overloads_rule)

    model.one_dir_cstr = Constraint(model.lines, rule=one_direction_rule)
    model.topology_cstr_2 = Constraint(model.buses, rule=topology_rule_2)

    model.bus_active_power_balance_cstr = Constraint(model.periods, model.buses, rule=bus_active_power_balance_rule)
    model.bus_reactive_power_balance_cstr = Constraint(model.periods, model.buses, rule=bus_reactive_power_balance_rule)
    model.sun_power_cstr_1 = Constraint(model.periods, model.buses, rule=sun_power_rule_1)
    model.sun_power_cstr_2 = Constraint(model.periods, model.buses, rule=sun_power_rule_2)
    model.sun_power_cstr_3 = Constraint(model.periods, model.buses, rule=sun_power_rule_3)
    model.inv_limit_cstr = Constraint(model.periods, model.buses, rule=inv_limit_rule)
    model.pv_production_cstr = Constraint(model.periods, model.buses, rule=pv_production_rule)
    model.inverter_cost_cstr = Constraint(rule=inverter_cost_rule)
    model.PV_cost_cstr = Constraint(rule=PV_cost_rule)
    model.PV_surf_limit_cstr = Constraint(model.buses, rule=PV_surf_limit)

    model.energy_imp_cost_cstr = Constraint(model.periods, rule=energy_imp_cost_rule)
    model.energy_exp_cost_cstr = Constraint(model.periods, rule=energy_exp_cost_rule)


    if lin_type != 0:
        model.complex_power_cstr = Constraint(model.periods, model.lines, rule=complex_power_rule)

        model.active_power_scomposition_cstr = Constraint(model.periods, model.lines, rule=active_power_scomposition_rule)
        model.reactive_power_scomposition_cstr = Constraint(model.periods, model.lines, rule=reactive_power_scomposition_rule)

        model.active_power_discr_cstr = Constraint(model.periods, model.lines, rule=active_power_discr_rule)
        model.reactive_power_discr_cstr = Constraint(model.periods, model.lines, rule=reactive_power_discr_rule)

        model.active_power_discr_limit_cstr = Constraint(model.periods, model.lines ,model.NPWB, rule=active_power_discr_limit_rule)
        model.reactive_power_discr_limit_cstr = Constraint(model.periods, model.lines ,model.NPWB, rule=reactive_power_discr_limit_rule)

    else:
        model.complex_power_cstr = Constraint(model.periods, model.lines, rule=conic_complex_power_rule)

    model.voltage_lim_1_cstr = Constraint(model.periods, model.B, rule=voltage_lim_1_rule)
    model.voltage_lim_2_cstr = Constraint(model.periods, model.B, rule=voltage_lim_2_rule)

    model.losses_calc_cstr = Constraint(model.periods, model.lines, rule=losses_rule)

    model.pv_inst_cstr = Constraint(model.buses, rule=PV_investment_rule)

    model.investment_cost_cstr = ConstraintList()
    model.investment_cost_cstr.add(PV_inv_cost_rule(model))
    model.investment_cost_cstr.add(hv_subs_inv_cost_rule(model))
    model.investment_cost_cstr.add(mv_subs_inv_cost_rule(model))

    def objective_rule(m):
        return 1/INV_HORIZON_DSO * (m.C_subs + m.C_cond + m.C_inv + m.C_PV + m.PV_inst_cost + m.subs_hv_inst_cost + m.subs_mv_inst_cost) + ALPHA * sum(m.C_electricity[p] + m.C_losses[p] + OMEGA * m.phi[p] for p in m.periods)

    model.objective_rule = Objective(rule=objective_rule, sense=minimize)

    # Solve the model
    
    solver = SolverFactory('gurobi')
    model.write("model.lp", io_options={"symbolic_solver_labels": True})

    solver.options['MIPGap'] = 0.001
    solver.options['Presolve'] = 2
    solver.options['FeasibilityTol'] = 0.001
    solver.options['NumericFocus'] = 2
    solver.options['ScaleFlag'] = 2  # Enable scaling
    solver.options['TimeLimit'] = 3600
    solver.options['Heuristics'] = 0.3

    results = solver.solve(model, tee=True, logfile="solver_report.log")

    # Combine solver log & solution summary in one file
    with open("optimization_report.txt", "w") as f:
        f.write("=== SOLVER LOG ===\n")
        with open("solver_report.log", "r") as log:
            f.write(log.read())  # Append solver output

        f.write("\n=== SOLUTION SUMMARY ===\n")
        results.write(ostream=f)  # Append results summary
        model.display(ostream=f)  # Append model variables and constraints

    # Example usage:
    execution_time, solver_status, gap, best_objective, best_bound, warnings = parse_solver_log('solver_report.log')
    logg = {
        'execution_time': execution_time,
        'solver_status': solver_status,
        'gap': gap,
        'best_objective': best_objective,
        'best_bound': best_bound,
        'warnings': warnings
    }


    plot_opt(model, LBUS, SUBS, SLACK, LINES, LINES_OPT, N_PERIODS)
    
    return model, logg