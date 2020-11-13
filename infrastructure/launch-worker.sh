#!/bin/bash
#SBATCH --job-name=dask-worker
#SBATCH --account=pi-moyer
#SBATCH --nodes=1
#SBATCH --time=03:30:00
#SBATCH --mem=15G
#SBATCH --cpus-per-task=6
#SBATCH --partition=broadwl
#SCRATCH --output=dask_worker.out
#SCRATCH --error=dask_worker.err

PATH_TO_SCHEDULER_FILE=${SCRATCH}/scheduler.json
PATH_TO_DASK=${SCRATCH}/reanalysis_env/bin

$PATH_TO_DASK/dask-worker --scheduler-file $PATH_TO_SCHEDULER_FILE \
	    --nthreads 6 \
	    --memory-limit 15.00GB \
	    --local-directory $SCRATCH \
	    --interface ib0 

