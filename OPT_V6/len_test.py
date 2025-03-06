import numpy as np
from utils import log_interval_length

b_values = [2.72, 10, 27.2]
n = 10
max_power = 212

for b in b_values:
    print(f"Base: {b}")
    for block in range(1, n+1):
        interval = log_interval_length(max_power, n, block, base=b)
        print(f"Block {block}: {interval:.20f}")

    print("-" * 30)

