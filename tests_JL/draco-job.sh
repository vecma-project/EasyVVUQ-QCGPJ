#!/bin/bash -l
# Standard output and error:
#SBATCH -o test.out.%j
#SBATCH -e test.err.%j
# Initial working directory:
#SBATCH -D ./
# Job Name:
#SBATCH -J uq_test
# Queue (Partition):
#SBATCH --partition=general
# Number of nodes and MPI tasks per node:
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=4
#
#SBATCH --mail-type=none
#SBATCH --mail-user=ljala@rzg.mpg.de
#
# Wall clock limit:
#SBATCH --time=00:30:00

# Run the program in uq folder
python test_cooling_pj_sl.py > test.log.${SLURM_JOBID}
