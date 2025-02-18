def test(BUS, LINES):
    number_slack = 0
    number_sub = 0
    number_lv_load = 0
    number_mv_load = 0

    for bus in BUS:
        if BUS[bus].b_type == 'HV_sub':
            number_slack += 1
        elif BUS[bus].b_type == 'MV_sub':
            number_sub += 1
        elif BUS[bus].b_type == 'LV_load':
            print(BUS[bus].load_kW)
            number_lv_load += 1
        elif BUS[bus].b_type == 'MV_load':
            number_mv_load += 1

    print("\nSystem Summary:")
    print("=========================")
    print(f"High Voltage Substations : {number_slack}")
    print(f"Medium Voltage Substations: {number_sub}")
    print(f"Low Voltage Loads        : {number_lv_load}")
    print(f"Medium Voltage Loads     : {number_mv_load}")
    print("=========================\n")

    
