import math
def obtain_coef(n):
    # Adjust the angle to rotate the first vertex to the positive y-axis
    angle_offset = math.pi / 2  # 90 degrees in radians

    # Compute coefficients for n-sided polygon with the first vertex on the positive y-axis
    coefficients = [(round(math.cos((k * 2 * math.pi / n) + angle_offset), 6),  
                    round(math.sin((k * 2 * math.pi / n) + angle_offset), 6))  
                    for k in range(n)]
            
    # Compute the correct scale factor
    scale_factor = 1 / math.cos(math.pi / n)

    return coefficients, scale_factor

print(obtain_coef(16))