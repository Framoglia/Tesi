from utils import *

weights = [1,2,3,4]

for p in range(1,len(weights)*24+1):
    weight = get_weights(p,weights)
    print(f'p = {p} --> w = {weight}')
    