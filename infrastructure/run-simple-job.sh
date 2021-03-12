#!/bin/bash

#SBATCH --job-name=dask-jetstream
#SBATCH --account=pi-moyer
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=140G
#SBATCH --time=00:10:00
#SBATCH --partition=bigmem2
#SBATCH --output=dask_scheduler.out
#SBATCH --error=dask_scheduler.err

PATH_TO_PROJECT='/project2/moyer/jetstream'
PATH_TO_REPO='/home/ivanhigueram/reanalysis_getter'

module load python
conda activate reanalysis_env

python ${PATH_TO_REPO}/infrastructure/runner.py \
       --product_path ${PATH_TO_PROJECT}/era-5-data/subset_data/ds_1979_2021_lat_20_1D_renamed.nc \
       --save_path ${PATH_TO_PROJECT}/era5_processed_data \
       --start_year 1990 \
       --end_year 2000 \
       --time_step 1


