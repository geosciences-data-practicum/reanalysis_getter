#!/bin/bash
#SBATCH --job-name=dask-worker
#SBATCH --account=geos39650
#SBATCH --nodes=1
#SBATCH --time=01:00:00
#SBATCH --partition=broadwl

PATH_TO_SCHEDULER_FILE=${HOME}/reanalysis_env/scheduler.json
PATH_TO_DASK=${SCRATCH}/reanalysis_env/bin

dask-worker --scheduler-file scheduler.json \
	    --memory-limit 10e9 \
	    --interface ib0 \
	    --local-directory ${HOME}

sleep infinity

