#!/bin/bash
#SBATCH --time=00:05:00                   # time limits
#SBATCH --nodes=1                         # nodes
#SBATCH --ntasks-per-node=4               # tasks per node
###SBATCH --cpus-per-task=1               # CPU per task
###SBATCH --mem=118GB                     # memory (max 180GB/node in skl_fua)
#SBATCH --partition=skl_fua_dbg           # partition to be used
###SBATCH --qos=                          # quality of service
#SBATCH --job-name=MFW                    # job name
#SBATCH --err=test-%j.err                 # std-error file
#SBATCH --out=test-%j.out                 # std-output file
#SBATCH --account=FUA33_UQMWA 			      # account number
#SBATCH --mail-type=END				            # specify email notification
#SBATCH --mail-user=ljala@ipp.mpg.de	    # e-mail address

export CPO_INPUT_DIR=AUG_28906_4/


#module load intel intelmpi mkl fftw 

python3 test_cooling_pj_sl.py > test-log.${SLURM_JOBID}
