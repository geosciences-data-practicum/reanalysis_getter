#!/bin/bash
#SBATCH --job-name=dask-worker
#SBATCH --account=geos39650
#SBATCH --nodes=1
#SBATCH --time=01:00:00
#SBATCH --mem=20G
#SBATCH --cpus-per-task=4
#SBATCH --partition=broadwl
#SCRATCH --output=dask_worker.out
#SCRATCH --error=dask_worker.err

PATH_TO_SCHEDULER_FILE=${SCRATCH}/scheduler.json
PATH_TO_DASK=${SCRATCH}/reanalysis_env/bin

$PATH_TO_DASK/dask-worker --scheduler-file $PATH_TO_SCHEDULER_FILE \
	    --nthreads 4 \
	    --memory-limit 20.00GB \
	    --local-directory $SCRATCH \
	    --interface ib0 

