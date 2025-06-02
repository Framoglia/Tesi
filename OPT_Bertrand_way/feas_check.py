import gurobipy as gp

# Load the model from the .lp file
m = gp.read("model.lp")

m.optimize()

# Check if the model is infeasible or ambiguous (INF_OR_UNBD)
if m.status in [gp.GRB.INFEASIBLE, gp.GRB.INF_OR_UNBD]:
    # If INF_OR_UNBD, disable dual reductions to clarify infeasibility:
    if m.status == gp.GRB.INF_OR_UNBD:
        m.reset()
        m.setParam('DualReductions', 0)
        m.optimize()

    if m.status == gp.GRB.INFEASIBLE:
        print("Model is infeasible. Computing IIS...")
        m.computeIIS()
        m.write("model.ilp")
        print("IIS information written to 'model.ilp'.")
