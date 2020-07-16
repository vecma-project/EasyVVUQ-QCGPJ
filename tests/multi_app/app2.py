#!/usr/bin/env python3
import sys
import json
import numpy as np
from model import eqt


# read inputs and call the model
json_input = sys.argv[1]
with open(json_input, "r") as f:
    inputs = json.load(f)

b0 = float(inputs['b0'])
b1 = float(inputs['b1'])
x = np.linspace(0, 1, 101)
u2 = eqt(x, b0, b1)

# output csv file
output_filename = inputs['out_file']
header = 'u2'
np.savetxt(output_filename, u2,
           delimiter=",",
           comments='',
           header=header)
