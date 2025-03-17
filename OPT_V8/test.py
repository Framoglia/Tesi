import numpy as np

def log_interval_length(b, n, i, base=2.72, epsilon=0.0001, a=0):
    """
    Computes the length of the i-th interval when dividing the range [a, b] logarithmically into n intervals.
    
    The division follows a logarithmic scale, meaning each interval grows exponentially.
    The interval index `i` starts from 1 (not 0), and the function returns the size of the i-th interval.

    Parameters:
    - a (float): The start of the range (must be > 0 for logarithmic scaling).
    - b (float): The end of the range (must be > a).
    - n (int): The total number of intervals.
    - i (int): The interval index (1-based, meaning it ranges from 1 to n).
    - base (float, optional): The logarithm base (default is 10). Use `np.e` for natural logarithm.

    Returns:
    - float: The length of the i-th interval.

    Raises:
    - ValueError: If `i` is not in the range [1, n].

    Example Usage:
    ```python
    a, b, n = 1, 1000, 5
    for i in range(1, n + 1):
        print(f"Interval {i}: Length = {log_interval_length(a, b, n, i)}")
    ```
    """
    if i < 1 or i > n:
        raise ValueError("Index i must be in range 1 to n")
    
    a = a + epsilon
    b = b + epsilon

    log_a = np.log(a) / np.log(base)  # Log-scale start
    log_b = np.log(b) / np.log(base)  # Log-scale end
    
    delta_L = (log_b - log_a) / n  # Logarithmic step size
    
    x_start = base ** (log_a + (i - 1) * delta_L)  # Start of interval i
    x_end = base ** (log_a + i * delta_L)  # End of interval i
    
    return x_end - x_start  # Interval length

# Test the function with example values


voltage_level = 'LV'
b = 0.2226 if voltage_level == 'LV' else 8.343
n = 15

for i in range(1, n + 1):
    print(f"Interval {i}: Length = {log_interval_length(b, n, i)}")
