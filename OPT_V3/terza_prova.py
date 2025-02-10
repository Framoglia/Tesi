from param import *
from pyomo.environ import *
from import_file import Bus

def optimize(LBUS, SUBS, LINES, LINES_OPT, N_PERIODS):

    ALPHA = 365/N_PERIODS*24
    model = ConcreteModel()

    #Sets that allow to define one variable for each entry

    model.periods = RangeSet(N_PERIODS)
    model.conductors = Set(initialize=LINES_OPT.keys()) 
    model.lines = Set(initialize=LINES.keys())  
    model.buses = Set(initialize=LBUS.keys())
    model.subs = Set(initialize=SUBS.keys())

    model.B = model.subs|model.buses 
    print("Sets defined successfully!")

    #Variables

    model.C_cond = Var(within=NonNegativeReals)  
    model.C_subs = Var(within=NonNegativeReals)  
    model.C_losses = Var(model.periods, within=NonNegativeReals)  

    model.line_opt = Var(model.lines, model.conductors, within=Binary)  #If the linesis activated wich option is chosen ?
    model.line_act = Var(model.lines, within=Binary) # Is the linesactivated ?

    model.subs_capacity = Var(model.subs, within=NonNegativeReals)
    model.subs_S = Var(model.periods, model.subs, within=NonNegativeReals)
    model.subs_P = Var(model.periods, model.subs, within=NonNegativeReals)
    model.subs_Q = Var(model.periods, model.subs, within=NonNegativeReals)
    model.beta = Var(model.subs, within=Binary)

    model.current_squared_k = Var(model.periods, model.lines, model.conductors, within=NonNegativeReals)
    model.current_squared = Var(model.periods, model.lines, within=NonNegativeReals)
    model.current_slack = Var(model.periods, model.lines, model.conductors, within=NonNegativeReals)
    model.line_overload = Var(model.periods, model.lines, model.conductors, within=Binary)
    model.phi = Var(model.periods, within=NonNegativeReals)

    model.active_power_k = Var( model.periods,model.lines, model.conductors, within=NonNegativeReals)
    model.active_power = Var(model.periods, model.lines, within=NonNegativeReals)

    model.reactive_power_k = Var(model.periods, model.lines, model.conductors, within=NonNegativeReals)
    model.reactive_power = Var(model.periods, model.lines, within=NonNegativeReals)

    model.voltage_squared = Var(model.periods, model.B, within=NonNegativeReals)

    model.p_imp = Param(model.periods, model.buses, mutable=True)
    model.q_imp = Param(model.periods, model.buses, mutable=True)

    print("Variables defined successfully!")
    #Parameters (this will come from the user sizing)

    for p in model.periods:
        for b in model.buses:  
            #Check if `b` exists in LBUS
            if b in LBUS:

                #Check if `LBUS[b]` is actually a `Bus` object
                if isinstance(LBUS[b], Bus):

                    #Check if `load_MVAR` is NOT None
                    if LBUS[b].load_MVAR:

                        #Check if `p-1` is a valid index
                        if 0 <= p-1 < len(LBUS[b].load_MVAR):
                            model.p_imp[p, b] = LBUS[b].load_MW[p-1]
                            model.q_imp[p, b] = LBUS[b].load_MVAR[p-1]
                        else:
                            print(f"Skipping p={p}, b={b}: Index {p-1} out of range for load_MVAR")

                    else:
                        print(f"Skipping p={p}, b={b}: load_MVAR is None or empty")

                else:
                    print(f"Skipping p={p}, b={b}: LBUS[{b}] is not a Bus object (type={type(LBUS[b])})")

            else:
                print(f"Skipping p={p}, b={b}: Bus ID {b} not found in LBUS")


    print("Loads defined successfully!")


    #Constraints

    def conductors_cost(m):
        return m.C_cond == sum(m.line_opt[l, c] * LINES_OPT[c].cost_keur_per_km * LINES[l].length for l in m.lines for c in m.conductors)

    def substation_cost(m):
        return m.C_subs == sum(UNIT_COST_SUBS*m.subs_capacity[s] for s in m.subs)

    def loss_cost(m,p):
        return m.C_losses[p] == sum(LINES_OPT[c].r_per_km * LINES[l].length * m.current_squared_k[p,l,c] for l in m.lines for c in m.conductors) * UNIT_COST_LOSSES

    def budget_balance(m):
        return (1+DISCOUNT_RATE)**INV_HORIZON_DSO * (m.C_cond + m.C_subs) + INV_HORIZON_DSO * ALPHA *sum(m.C_losses[p] for p in m.periods) <= INV_HORIZON_DSO * ALPHA * sum(m.p_imp[p,b] for b in m.buses for p in m.periods)*ENERGY_COST * DELTA_T

    def active_power_rule(m,p,l):
        return m.active_power[p,l] == sum(m.active_power_k[p,l,c] for c in m.conductors)

    def reactive_power_rule(m,p,l):
        return m.reactive_power[p,l] == sum(m.reactive_power_k[p,l,c] for c in m.conductors)

    def curent_squared_rule(m,p,l):
        return m.current_squared[p,l] == sum(m.current_squared_k[p,l,c] for c in m.conductors)

    def active_power_subs_rule(m,p,s):    #Ha senso mettere per ogni linea???
        return m.subs_P[p,s] == -(sum(m.active_power_k[p,l,c] - m.current_squared_k[p,l,c] * LINES_OPT[c].r_per_km * LINES[l].length for c in m.conductors for l in m.lines if LINES[l].to_bus==s) - sum(m.active_power_k[p,l,c] for c in m.conductors for l in m.lines if LINES[l].from_bus==s))

    def reactive_power_subs_rule(m,p,s):
        return m.subs_Q[p,s] == -(sum(m.reactive_power_k[p,l,c] - m.current_squared_k[p,l,c] * LINES_OPT[c].xl_per_km * LINES[l].length for c in m.conductors for l in m.lines if LINES[l].to_bus==s) - sum(m.reactive_power_k[p,l,c] for c in m.conductors for l in m.lines if LINES[l].from_bus==s))

    def active_power_lbus_rule(m,p,b):
        return m.p_imp[p,b]  == (sum(m.active_power_k[p,l,c] - m.current_squared_k[p,l,c] * LINES_OPT[c].r_per_km * LINES[l].length for c in m.conductors for l in m.lines if LINES[l].to_bus==b) - sum(m.active_power_k[p,l,c] for c in m.conductors for l in m.lines if LINES[l].from_bus==b))

    def reactive_power_lbus_rule(m,p,b):
        return m.q_imp[p,b]  == (sum(m.reactive_power_k[p,l,c] - m.current_squared_k[p,l,c] * LINES_OPT[c].xl_per_km * LINES[l].length for c in m.conductors for l in m.lines if LINES[l].to_bus==b) - sum(m.reactive_power_k[p,l,c] for c in m.conductors for l in m.lines if LINES[l].from_bus==b))

    def voltage_rule_1(m,p,l):
        i = LINES[l].from_bus
        j = LINES[l].to_bus
        return m.voltage_squared[p,j] - m.voltage_squared[p,i] <= sum(-2 * (LINES_OPT[c].r_per_km * LINES[l].length * m.active_power_k[p,l,c] + LINES_OPT[c].xl_per_km * LINES[l].length * m.reactive_power_k[p,l,c]) + (LINES_OPT[c].r_per_km**2 + LINES_OPT[c].xl_per_km **2) * LINES[l].length**2 * m.current_squared_k[p,l,c] for c in m.conductors) + M * (1-m.line_act[l]) 

    def voltage_rule_2(m,p,l):
        i = LINES[l].from_bus
        j = LINES[l].to_bus
        return m.voltage_squared[p,j] - m.voltage_squared[p,i] >= sum(-2 * (LINES_OPT[c].r_per_km * LINES[l].length * m.active_power_k[p,l,c] + LINES_OPT[c].xl_per_km * LINES[l].length * m.reactive_power_k[p,l,c]) + (LINES_OPT[c].r_per_km**2 + LINES_OPT[c].xl_per_km **2) * LINES[l].length**2 * m.current_squared_k[p,l,c] for c in m.conductors) - M * (1-m.line_act[l]) 

    def complex_power_rule(m,p,l):
        return  m.voltage_squared[p,LINES[l].from_bus] * m.current_squared[p,l] >= m.active_power[p,l]**2 + m.reactive_power[p,l]**2

    def apparent_power_subs_rule(m,p,s):
        return m.subs_S[p,s]**2 >= m.subs_P[p,s]**2 + m.subs_Q[p,s]**2 

    def subs_capacity_rule(m,p,s):
        return m.subs_S[p,s] <= m.subs_capacity[s]

    def max_capacity_rule(m,s):
        return m.subs_capacity[s] <= m.beta[s] * SUBS[s].max_capacity

    def subs_voltage_rule_1(m,p,s):
        return m.voltage_squared[p,s] - 1 <= (MAX_VOLTAGE**2 - 1) * (1-m.beta[s])

    def subs_voltage_rule_2(m,p,s):
        return m.voltage_squared[p,s] - 1 >= (MIN_VOLTAGE**2 - 1) * (1-m.beta[s])

    def lbus_voltage_rule_1(m,p,l,c):
        j = LINES[l].to_bus
        if j in LBUS.keys():
            VOLTAGE_LEVEL = LBUS[j].voltage_level
        else:
            VOLTAGE_LEVEL = SUBS[j].voltage_level
        return m.active_power_k[p,l,c] <= m.line_opt[l,c] * LINES_OPT[c].imax_kA * VOLTAGE_LEVEL

    def lbus_voltage_rule_2(m,p,l,c):
        j = LINES[l].to_bus
        if j in LBUS.keys():
            VOLTAGE_LEVEL = LBUS[j].voltage_level
        else:
            VOLTAGE_LEVEL = SUBS[j].voltage_level
        return m.active_power_k[p,l,c] >= -m.line_opt[l,c] * LINES_OPT[c].imax_kA * VOLTAGE_LEVEL

    def lbus_voltage_rule_3(m,p,l,c):
        j = LINES[l].to_bus
        if j in LBUS.keys():
            VOLTAGE_LEVEL = LBUS[j].voltage_level
        else:
            VOLTAGE_LEVEL = SUBS[j].voltage_level
        return m.reactive_power_k[p,l,c] <= m.line_opt[l,c] * LINES_OPT[c].imax_kA * VOLTAGE_LEVEL

    def lbus_voltage_rule_4(m,p,l,c):
        j = LINES[l].to_bus
        if j in LBUS.keys():
            VOLTAGE_LEVEL = LBUS[j].voltage_level
        else:
            VOLTAGE_LEVEL = SUBS[j].voltage_level
        return m.reactive_power_k[p,l,c] >= -m.line_opt[l,c] * LINES_OPT[c].imax_kA * VOLTAGE_LEVEL

    def current_slack_rule(m,p,l,c):
        return m.current_slack[p,l,c] <= LINES_OPT[c].imax_kA **2 * m.line_overload[p,l,c]

    def current_slack_rule_2(m,p,l,c):
        return m.current_squared_k[p,l,c] - m.current_slack[p,l,c] <= LINES_OPT[c].imax_kA **2 * m.line_opt[l,c]

    def line_activation_rule(m,l):
        return m.line_act[l] == sum(m.line_opt[l,c] for c in m.conductors)

    def topology_rule(m):
        return sum(m.line_act[l] for l in m.lines) == len(LBUS.keys())

    def total_overloads_rule(m,p):
        return sum(m.line_overload[p,l,c] for l in m.lines for c in m.conductors) == m.phi[p]



    print("Constrained defined successfully!")

    model.conductors_cost = Constraint(rule=conductors_cost)
    model.substation_cost = Constraint(rule=substation_cost)
    model.loss_cost = Constraint(model.periods, rule=loss_cost)
    model.budget_balance = Constraint(rule=budget_balance)
    model.active_power_rule = Constraint(model.periods, model.lines, rule=active_power_rule)
    model.reactive_power_rule = Constraint(model.periods, model.lines, rule=reactive_power_rule)
    model.curent_squared_rule = Constraint(model.periods, model.lines, rule=curent_squared_rule)
    model.active_power_subs_rule = Constraint(model.periods, model.subs, rule=active_power_subs_rule)
    model.reactive_power_subs_rule = Constraint(model.periods, model.subs, rule=reactive_power_subs_rule)
    model.active_power_lbus_rule = Constraint(model.periods, model.buses, rule=active_power_lbus_rule)
    model.reactive_power_lbus_rule = Constraint(model.periods, model.buses, rule=reactive_power_lbus_rule)
    model.voltage_rule_1 = Constraint(model.periods, model.lines, rule=voltage_rule_1)
    model.voltage_rule_2 = Constraint(model.periods, model.lines, rule=voltage_rule_2)
    model.complex_power_rule = Constraint(model.periods, model.lines, rule=complex_power_rule)
    model.apparent_power_subs_rule = Constraint(model.periods, model.subs, rule=apparent_power_subs_rule)
    model.subs_capacity_rule = Constraint(model.periods, model.subs, rule=subs_capacity_rule)
    model.max_capacity_rule = Constraint(model.subs, rule=max_capacity_rule)
    model.subs_voltage_rule_1 = Constraint(model.periods, model.subs, rule=subs_voltage_rule_1)
    model.subs_voltage_rule_2 = Constraint(model.periods, model.subs, rule=subs_voltage_rule_2)
    model.lbus_voltage_rule_1 = Constraint(model.periods, model.lines, model.conductors, rule=lbus_voltage_rule_1)
    model.lbus_voltage_rule_2 = Constraint(model.periods, model.lines, model.conductors, rule=lbus_voltage_rule_2)
    model.lbus_voltage_rule_3 = Constraint(model.periods, model.lines, model.conductors, rule=lbus_voltage_rule_3)
    model.lbus_voltage_rule_4 = Constraint(model.periods, model.lines, model.conductors, rule=lbus_voltage_rule_4)
    model.current_slack_rule = Constraint(model.periods, model.lines, model.conductors, rule=current_slack_rule)
    model.current_slack_rule_2 = Constraint(model.periods, model.lines, model.conductors, rule=current_slack_rule_2)
    model.line_activation_rule = Constraint(model.lines, rule=line_activation_rule)
    model.topology_rule = Constraint(rule=topology_rule)
    model.total_overloads_rule = Constraint(model.periods, rule=total_overloads_rule)


    print("Constraint assigned successfully!")

    def objective_rule(m):
        return 1/INV_HORIZON_DSO * (m.C_subs + m.C_cond) + ALPHA* sum(m.C_losses[p] + OMEGA * m.phi[p] for p in m.periods)

    model.objective_rule = Objective(rule=objective_rule, sense=minimize)

    print("Objective assigned successfully!")

    print("Model created successfully!")
    print("Model is being solved...")

    # Solve the model
    solver = SolverFactory('gurobi')
    results = solver.solve(model, tee=True)

    # Check the solver status
    if results.solver.status == SolverStatus.ok and results.solver.termination_condition == TerminationCondition.optimal:
        print("Solver found an optimal solution.")
    else:
        print("Solver did not find an optimal solution.")
        exit()

    # Now, you can plot the results using the plot_opt function
    from utils import plot_opt
    plot_opt(model, LBUS, SUBS, LINES, LINES_OPT, N_PERIODS)
