#!/bin/bash
set -e

PATH_TO_RAW_MODEL=$1
PATH_TO_SAVE=$2
NUMBER_OF_WORKERS=$3

echo "Launching dask scheduler"
s=`sbatch launch-dask-scheduler.sh | cut -d " " -f 4`
sjob=${s%.*}
echo ${s}

echo "Launching dask workers (${workers})"
sbatch $SFLAGS --array=0-${NUMBER_OF_WORKERS} launch-worker.sh

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
./runner.py --product_path $PATH_TO_RAW_MODEL \
	    --save_path $PATH_TO_SAVE \
	    --time_step 5
