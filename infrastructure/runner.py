import os
import click
import time
import xarray as xr
from pathlib import Path
from datetime import datetime
from dateutil.relativedelta import relativedelta

from jetstream.model.model import Model
from dask.distributed import Client


@click.command()
@click.option('--product_path', help='Path to model data')
@click.option('--save_path', help='Path to save output')
@click.option('--time_step', default=5, help='Number of years per file')
def calculate_t_prime(product_path,
                      save_path,
                      start_year=2015,
                      end_year=2100,
                      time_step):
    """
    Calculate all methods from paper for a specified model by years

    Since we are memory constrained, this function takes the jetstream.Model
    object and allow to run the methods pipeline for a user defined group of
    years. The time_step allow us to define the width of the year window. 

    Arguments: 
    - product_path: str path to raw model in NetCDF format.
    - save_path: str path to save output data from modeling
    - start_year: int start year. 2015 is set as default following GCM models
    - end_year: int end year. 2100 is set as default following GCM models
    - time_step: int Define a step to divide years. 5 is the default value.

    Returns: 
    None. Save to path directly.
    """

    print(f'Initializing t prime calculation')

    for year in range(start_year, end_year, time_step):
        # Define time ranges 
        start_year = datetime(year, 12, 1).strftime('%Y-%m-%d')
        end_year = datetime(year + time_step, 3, 1).strftime('%Y-%m-%d')
        subset_data = {'time': slice(start_year, end_year)}

        print(f"Start processing -- {start_year} to {end_year}")
        model_object = Model(
            path_to_files=product_path,
            path_to_save_files=save_path,
            subset_dict=subset_data
        )

        model_object.pipeline_methods


if __name__ == '__main__':
    path_to_scheduler = os.path.join(os.getenv('HOME'),
                                 'reanalysis_env',
                                 'scheduler.json')
    client = Client(scheduler_file=path_to_scheduler)
    calculate_t_prime()

