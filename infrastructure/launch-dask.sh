#!/bin/bash
set -e

PATH_TO_RAW_MODEL=$1
NUMBER_OF_WORKERS=$2

SFLAGS="--account=geos39650 --partition=broadwl"

echo "Launching dask scheduler"
s=`sbatch $SFLAGS launch-dask-scheduler.sh | cut -d " " -f 4`
sjob=${s%.*}
echo ${s}

echo "Launching dask workers (${workers})"
sbatch $SFLAGS --array=0-${NUMBER_OF_WORKERS} launch-dask-worker.sh

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

# Launcing model
echo "Launching model in workers"
./runner.py --product_path $1 \
	    ---save_path $2 \
	    --time_step 5
