import math

def obtain_coef(n):
    # Compute coefficients for n-sided polygon
    coefficients = [(round(math.cos(k * 2 * math.pi / n), 5), 
                     round(math.sin(k * 2 * math.pi / n), 5)) 
                    for k in range(n)]
    
    # Compute the correct scale factor
    scale_factor = 1 / math.cos(math.pi / n)

    return coefficients, scale_factor

# Example usage
print(obtain_coef(4))  # Should give a square
print(obtain_coef(6))  # Should give a hexagon
print(obtain_coef(16)) # Should give a hexadecagon
