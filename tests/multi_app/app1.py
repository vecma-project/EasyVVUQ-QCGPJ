#!/usr/bin/env python3
import sys
import json
import numpy as np
from model import eqt


# read inputs and call the model
json_input = sys.argv[1]
with open(json_input, "r") as f:
    inputs = json.load(f)

a0 = float(inputs['a0'])
a1 = float(inputs['a1'])
x = np.linspace(0, 1, 101)
u1 = eqt(x, a0, a1)

# output csv file
output_filename = inputs['out_file']
header = 'u1'
np.savetxt(output_filename, u1,
           delimiter=",",
           comments='',
           header=header)
