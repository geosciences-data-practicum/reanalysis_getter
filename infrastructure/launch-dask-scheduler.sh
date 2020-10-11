#!/bin/bash

#SBATCH --job-name=dask-jetstream
#SBATCH --account=geos39650
#SBATCH --nodes=1
#SBATCH --time=04:00:00
#SBATCH --partition=broadwl
#SBATCH --mail-user ivanhigueram@uchicago.edu
#SBATCH --mail-type=ALL

# This writes a scheduler.json file into your home directory
# You can then connect with the following Python code
# >>> from dask.distributed import Client
# >>> client = Client(scheduler_file='~/scheduler.json')

PATH_TO_SCHEDULER_FILE=${HOME}/reanalysis_env/scheduler.json
PATH_TO_DASK=${SCRATCH}/reanalyis_env/bin

rm -f PATH_TO_SCHEDULER_FILE

$PATH_TO_DASK/dask-scheduler --scheduler-file $PATH_TO_SCHEDULER_FILE \
	--interface ib0 \ 
	--local-directory ${HOME} &

for i in {1..4}; do
    dask-worker --scheduler-file $PATH_TO_SCHEDULER_FILE \
	    --memory-limit 32e9 \
	    --interface ib0  
done

sleep infinity

