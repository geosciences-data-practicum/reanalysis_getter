#!/bin/bash

#SBATCH --job-name=dask-jetstream
#SBATCH --account=pi-moyer
#SBATCH --nodes=1
#SBATCH --exclusive
#SBATCH --time=04:00:00
#SBATCH --partition=broadwl
#SBATCH --mail-user ivanhigueram@uchicago.edu
#SBATCH --mail-type=ALL
#SBATCH --output=dask_scheduler.out
#SBATCH --error=dask_scheduler.err

# This writes a scheduler.json file into your home directory
# You can then connect with the following Python code
# >>> from dask.distributed import Client
# >>> client = Client(scheduler_file='~/scheduler.json')

PATH_TO_SCHEDULER_FILE=${SCRATCH}/scheduler.json
PATH_TO_DASK=${SCRATCH}/reanalysis_env/bin

rm -f PATH_TO_SCHEDULER_FILE

$PATH_TO_DASK/dask-scheduler --scheduler-file $PATH_TO_SCHEDULER_FILE \
	--interface ib0 

while [ ! -f $SCHEDULER ]; do 
	    sleep 1
    done

