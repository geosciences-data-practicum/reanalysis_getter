#!/bin/bash

#SBATCH --job-name=dask-mpi
#SBATCH --account=geos39650
#SBATCH --nodes=1
#SBATCH --time=72:00:00
#SBATCH --partition=broadwl

# SBATCH template for Berkeley Computing Savio
# Scheduler: SLURM

# This writes a scheduler.json file into your home directory
# You can then connect with the following Python code
# >>> from dask.distributed import Client
# >>> client = Client(scheduler_file='~/scheduler.json')

PATH_TO_DASK=${SCRATCH}/${USER}/reanalyis_env/bin
rm -f scheduler.json

$PATH_TO_DASK/dask-scheduler --scheduler-file scheduler.json --interface ib0 --local-directory ${HOME} &

for i in {1..4}; do
    dask-worker --scheduler-file scheduler.json --memory-limit 32e9 --interface ib0 --local-directory ${USER} &
done

sleep infinity

