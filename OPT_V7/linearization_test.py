def linearization_possibilities():
    """
    Assemble your linearization possiblilities:

    lin[0] => Complex power constraint
                0 Conic
                1 Lin with equal length blocks
                2 Lin with log lenght block

    lin[1] => Number of block for power linearization

    lin[2] => Type of Substation limits
                0 Conic
                1 Linearized ext (mult = scale_factor)
                2 Linearized int (mult = 1)

    lin[3] => Number of segments for linearization
    """

    lin_test = {}
    lin_test[0] = [2,10,1,16] #70, 104, 106, 129
    lin_test[1] = [2,15,1,16] #75, 99, 101 
    """lin_test[2] = [1,10,1,16] #un botto
    lin_test[3] = [1,15,1,16] #prob un botto"""
    lin_test[4] = [0,10,1,16] #105, 137, 133


    return lin_test


