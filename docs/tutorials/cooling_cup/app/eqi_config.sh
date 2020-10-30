#!/bin/bash

# Load required modules
module load python/3.7.3

# Initiate virtualenv
. ~/.virtualenvs/easyvvuq-qcgpj/bin/activate

# Set the COOLING_APP environment variable to point to the cooling application directory
export COOLING_APP=~/tutorials/cooling_cup/app/cooling

# For execution on clusters set the SCRATCH environment variable to point
# to a directory shared across all computing nodes, e.g. for the Eagle cluster
# uncomment the following line:
# export SCRATCH=$PLG_USER_SCRATCH/$USER

# Do not change anything below

# Set environment variable for use by EasyVVUQ-QCGPJ integrator
export EQI_CONFIG="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
