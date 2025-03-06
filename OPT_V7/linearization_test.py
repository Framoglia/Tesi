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
    n_blocks = [5,10,15]
    lin_test[2] = [2,10,1,8]
    lin_test[3] = [2,10,1,16]
    lin_test[4] = [2,10,1,32]
    lin_test[5] = [2,10,0,None]
    return lin_test

