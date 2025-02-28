import math
def obtain_coef(n):
    coefficients = [(round(math.cos(k * math.pi / 8), 5), round(math.sin(k * math.pi / 8), 5)) for k in range(n)]
    
    scale_factor = 1 / math.cos(math.pi / 16)

    return coefficients, scale_factor


coefficients, scale_factor = obtain_coef(10)
print(coefficients)
