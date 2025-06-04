from param import *
from pyomo.environ import *
from utils import *
from pyomo.core import SOSConstraint


def optimize_log(LBUS, SUBS, SLACK, LINES, LINES_OPT, N_PERIODS):
    DATA = LBUS,SUBS, SLACK, LINES,LINES_OPT,N_PERIODS
    for line in LINES.keys():
        print(f"{line} --> {is_line_to_or_from_load(DATA, line)}")

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
    model.C_subs_hv = Var(within=NonNegativeReals)  
    model.C_subs_mv = Var(within=NonNegativeReals)  
    model.subs_hv_inst_cost = Var(within=NonNegativeReals)
    model.subs_mv_inst_cost = Var(within=NonNegativeReals)
    model.unserved_fictitious_power_cost = Var(within=NonNegativeReals)

    model.line_opt = Var(model.lines, model.conductors, within=Binary)  # Conductor chosen when line is active 
    model.line_act = Var(model.lines, within=Binary)                    # Is the line activated ?

    model.subs_hv_capacity = Var(model.subs_hv, within=NonNegativeReals)
    model.subs_hv_F = Var( model.subs_hv, within=Reals)
    model.beta = Var(model.subs_hv, within=Binary)

    model.subs_mv_capacity = Var(model.subs_mv, within=NonNegativeReals)
    model.gamma = Var(model.subs_mv, within=Binary)
    model.gamma_used = Var(model.subs_mv, within=Binary)  # Used to indicate if the substation is used in the topology

    model.fictitious_power_k = Var(model.lines, model.conductors, within=Reals)
    model.fictitious_power = Var(model.lines, within=Reals)
    model.unserved_fictitious_power = Var(model.buses, within=NonNegativeReals)

    #Constraints

    def conductors_cost(m):
        return m.C_cond == sum(m.line_opt[l, c] * LINES_OPT[c].cost_keur_per_km * LINES[l].length  / 100 for l in m.lines for c in m.conductors)  #eur

    def hv_substation_cost_rule(m):
        return m.C_subs_hv == sum(UNIT_COST_SUBS_HV * m.subs_hv_capacity[s] * BASE_POWER for s in m.subs_hv)
    
    def mv_substation_cost_rule(m):
        return m.C_subs_mv == sum(UNIT_COST_SUBS_MV * m.subs_mv_capacity[s] * BASE_POWER for s in m.subs_mv)
    
    def hv_subs_inv_cost_rule(m):
        return m.subs_hv_inst_cost == sum(m.beta[s] * INST_COST_HV_SUB for s in m.subs_hv)
    
    def mv_subs_inv_cost_rule(m):
        return m.subs_mv_inst_cost == sum(m.gamma[s] * INST_COST_MV_SUB for s in m.subs_mv)
    
    def fictitious_power_rule(m,l):
        return m.fictitious_power[l] == sum(m.fictitious_power_k[l,c] for c in m.conductors)

    def fictitious_power_subs_hv_rule(m,s):
        return m.subs_hv_F[s] == -(sum(m.fictitious_power_k[l,c] for c in m.conductors for l in m.lines if LINES[l].to_bus==s) - sum(m.fictitious_power_k[l,c] for c in m.conductors for l in m.lines if LINES[l].from_bus==s))
    
    def beta_switch_fict_rule(m,s):
        return m.beta[s] * len(LBUS.keys()) >= m.subs_hv_F[s]
    
    def fictitious_power_subs_mv_rule(m,s):
        relevant_lines = [l for l in m.lines if LINES[l].from_bus == s or LINES[l].to_bus==s]  
        if not relevant_lines:
            return Constraint.Feasible
        return 0 == -(sum(m.fictitious_power_k[l,c] for c in m.conductors for l in m.lines if LINES[l].to_bus==s) - sum(m.fictitious_power_k[l,c] for c in m.conductors for l in m.lines if LINES[l].from_bus==s))
    
    def fictitious_power_lbus_rule(m,b):
        return 1 - m.unserved_fictitious_power[b]  == (sum(m.fictitious_power_k[l,c] for c in m.conductors for l in m.lines if LINES[l].to_bus==b) - sum(m.fictitious_power_k[l,c] for c in m.conductors for l in m.lines if LINES[l].from_bus==b))
    
    def fictitious_power_subs_mv_lv_rule(m,s):
        return m.subs_mv_capacity[s] * OMEGA >= -(sum(m.fictitious_power_k[l,c] for c in m.conductors for l in m.lines if LINES[l].to_bus==s and is_line_from_LV_load(DATA, l)) - sum(m.fictitious_power_k[l,c] for c in m.conductors for l in m.lines if LINES[l].from_bus==s and is_line_to_LV_load(DATA, l)))

    def line_activation_rule(m,l):
        return m.line_act[l] == sum(m.line_opt[l,c] for c in m.conductors)
    
    def fictitious_power_activation_rule_lower(m,  l, c):
        return m.fictitious_power_k[ l, c] >= -m.line_opt[l, c] * len(LBUS.keys())
    
    def fictitious_power_activation_rule(m,  l, c):
        return m.fictitious_power_k[ l, c] <= m.line_opt[l, c] * len(LBUS.keys())
    
    def fictitious_power_cost_rule(m):
        return m.unserved_fictitious_power_cost == sum(m.unserved_fictitious_power[b] for b in m.buses) * OMEGA

    def sos1_line_opt_rule(m, l):
        return [m.line_opt[l, c] for c in m.conductors]
    
    def topology_rule(m):
        return sum(m.line_act[l] for l in m.lines if is_line_to_or_from_load(DATA, l)) == len(LBUS.keys())
    
    def topolgy_rule_2(m, s):
        relevant_lines = [l for l in m.lines if LINES[l].to_bus == s or LINES[l].from_bus == s]

        # If no relevant lines exist, skip constraint
        if not relevant_lines:
            return Constraint.Feasible

        # Filter out lines going to/from load (data only)
        lines_not_to_from_load = [l for l in relevant_lines if not is_line_to_or_from_load(DATA, l)]

        # If that filter removes all lines, skip constraint again
        if not lines_not_to_from_load:
            return Constraint.Feasible

        # Otherwise return symbolic Pyomo inequality
        expr = sum(m.line_act[l] for l in lines_not_to_from_load)
        return expr <= 1
    
    
    model.gamma_used = Var(model.subs_mv, within=Binary)
    model.abs_fict_p = Var(model.lines, within=NonNegativeReals)

    def abs_fict_rule(m,l):
        return m.abs_fict_p[l] >= m.fictitious_power[1,l]
    
    def abs_fict_rule_2(m,l):
        return m.abs_fict_p[l] >= -m.fictitious_power[1,l]

    def gamma_switch_fict_rule(m,s):
        return m.gamma_used[s] * OMEGA <= sum(m.abs_fict_p[l] for l in m.lines if LINES[l].to_bus==s)
    
    def topology_rule_3(m,s):
        return sum(m.line_act[l] for l in m.lines) == len(LBUS.keys()) + sum(m.beta[s] for s in m.subs_hv) + sum(m.gamma_used[s] for s in m.subs_mv) - 1


      


    model.conductors_cost = Constraint(rule=conductors_cost)
    model.hv_substation_cost_cstr = Constraint(rule=hv_substation_cost_rule)
    model.mv_substation_cost_cstr = Constraint(rule=mv_substation_cost_rule)
    model.hv_subs_inv_cost_cstr = Constraint(rule=hv_subs_inv_cost_rule)
    model.mv_subs_inv_cost_cstr = Constraint(rule=mv_subs_inv_cost_rule)
    model.fictitious_power_cstr = Constraint(model.lines, rule=fictitious_power_rule)
    model.fictitious_power_subs_hv_cstr = Constraint(model.subs_hv, rule=fictitious_power_subs_hv_rule)
    model.fictitious_power_subs_mv_cstr = Constraint(model.subs_mv, rule=fictitious_power_subs_mv_rule)
    model.fictitious_power_subs_mv_lv_cstr = Constraint(model.subs_mv, rule=fictitious_power_subs_mv_lv_rule)
    model.fictitious_power_lbus_cstr = Constraint(model.buses, rule=fictitious_power_lbus_rule)
    model.line_activation_cstr = Constraint(model.lines, rule=line_activation_rule)
    model.fictitious_power_activation_lower_cstr = Constraint(model.lines, model.conductors, rule=fictitious_power_activation_rule_lower)
    model.fictitious_power_activation_cstr = Constraint(model.lines, model.conductors, rule=fictitious_power_activation_rule)
    model.fictitious_power_cost_cstr = Constraint(rule=fictitious_power_cost_rule)
    model.beta_switch_fict_cstr = Constraint(model.subs_hv , rule=beta_switch_fict_rule)
    model.sos1_line_opt = SOSConstraint(model.lines, rule=sos1_line_opt_rule, sos=1)
    
    model.abs_fict_p_cstr = Constraint(model.lines, rule=abs_fict_rule)
    model.abs_fict_p_cstr_2 = Constraint(model.lines, rule=abs_fict_rule_2)
    model.gamma_switch_fict_cstr = Constraint(model.subs_mv, rule=gamma_switch_fict_rule)
    #model.topology_cstr = Constraint(rule=topology_rule)
    #model.topology_cstr_2 = Constraint(model.subs_mv, rule=topolgy_rule_2)
    model.topology_cstr_3 = Constraint(model.subs_mv, rule=topology_rule_3)

    def objective_rule(m):
        
        return 1/INV_HORIZON_DSO * (m.C_subs_hv + m.C_subs_mv + m.C_cond + m.subs_hv_inst_cost + m.subs_mv_inst_cost) + OMEGA * m.unserved_fictitious_power_cost

    model.objective_rule = Objective(rule=objective_rule, sense=minimize)

    # Solve the model
    
    solver = SolverFactory('gurobi')
    model.write("model.lp", io_options={"symbolic_solver_labels": True})

    """solver.options['Presolve'] = 2
    solver.options['RINS'] = 75
    solver.options['MIQCPMethod'] = 1
    solver.options['Cuts'] = 3
    solver.options['Heuristics'] = 0.05"""

    solver.options['TimeLimit'] = 60
    solver.options['MIPGap'] = 0.01
    solver.options['IntegralityFocus'] = 1
    solver.options['ScaleFlag'] = 0
    solver.options['Heuristics'] = 0.5
    solver.options['Method'] = 1

    """
    solver.options['MIPFocus'] = 1
    solver.options['ScaleFlag'] = 0
    solver.options['MIPFocus'] = 1
    solver.options['ImproveStartTime'] = 450
    solver.options['NumericFocus'] = 3"""
    



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
    
    return model, logg