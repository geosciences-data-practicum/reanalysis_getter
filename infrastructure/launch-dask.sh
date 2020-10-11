#!/bin/bash
set -e

SFLAGS="--account=geos39650 --partition=broadwl"

echo "Launching dask scheduler"
s=`sbatch $SFLAGS launch-dask-scheduler.sh | cut -d " " -f 4`
sjob=${s%.*}
echo ${s}

echo "Launching dask workers (${workers})"
sbatch $SFLAGS --array=0-6 launch-dask-worker.sh

squeue --job ${sjob}

# block until the scheduler job starts
while true; do
    status=`squeue --job ${sjob} | tail -n 1`
    echo ${status}
    if [[ ${status} =~ " R " ]]; then
        break
    fi
    sleep 1
done

if [[ -z $WORKDIR ]]; then
    WORKDIR=/local
fi

default=$HOME
notebook=${2:-$default}
echo "Setting up Jupyter Lab, Notebook dir: ${notebook}"

