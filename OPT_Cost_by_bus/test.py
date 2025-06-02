import dill
from debug import *
from validation import *
import pandapower as pp

def main(pkl_path):

    with open(pkl_path, "rb") as f:
        loaded_data = dill.load(f)

    model = loaded_data["model"]
    LBUS = loaded_data["LBUS"]
    SUBS = loaded_data["SUBS"]
    SLACK = loaded_data["SLACK"]
    LINES = loaded_data["LINES"]
    LINES_OPT = loaded_data["LINES_OPT"]
    N_PERIODS = loaded_data["N_PERIODS"]
    irradiation = loaded_data.get("irradiation")

    net, pp_bus_map, pp_line_map, results = export_and_solve(model, LBUS, SUBS, SLACK, LINES, LINES_OPT)

    for res in results.values() :
        pp.plotting.pf_res_plotly(res["net"])
        print(res["line"])
        break


main('model.pkl')