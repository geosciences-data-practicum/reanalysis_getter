#!/bin/bash
#SBATCH --job-name=dask-worker
#SBATCH --account=geos39650
#SBATCH --nodes=1
#SBATCH --time=01:00:00
#SBATCH --partition=broadwl

dask-worker --scheduler-file scheduler.json \
	--memory-limit 10e9 \
	--interface ib0 \
	--local-directory ${HOME}

sleep infinity

