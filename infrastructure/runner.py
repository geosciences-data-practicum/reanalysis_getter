import os
import click
import time
import xarray as xr
from pathlib import Path
from datetime import datetime
from dateutil.relativedelta import relativedelta

from jetstream.model.model import Model
from dask.distributed import Client


def calculate_t_prime(path_to_raw_file,
                      path_to_save,
                      start_year=1995,
                      end_year=2020,
                      size_year_range=5):
    """
    Calculate t_prime for the user-defined path and output a NetCDF file with
    the processed data
    """

    print(f'Initializing t prime calculation')

    for year in range(start_year, end_year, size_year_range):
        # Define time ranges 
        start_year = datetime(year, 12, 1).strftime('%Y-%m-%d')
        end_year = datetime(year + size_year_range, 3, 1).strftime('%Y-%m-%d')
        subset_data = {'time': slice(start_year, end_year)}

        print(f"Start processing -- {start_year} to {end_year}")
        model_object = 

            path_save = os.path.join(path_to_save, f'{out}_gcm_{start_year}_{end_year}.nc4')



if __name__ == '__main__':
    path_to_scheduler = os.path.join(os.getenv('HOME'),
                                 'reanalysis_env',
                                 'scheduler.json')
    client = Client(scheduler_file=path_to_scheduler)


