import dill
from debug import plot_network_solution_2

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

    plot_network_solution_2(model, LBUS, SUBS, SLACK, LINES, LINES_OPT)

main('OPT_V16/model.pkl')