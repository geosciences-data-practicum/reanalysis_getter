#!/usr/bin/env python

import os
import sys
import click
import time
import logging
import xarray as xr
from pathlib import Path
from datetime import datetime
from dateutil.relativedelta import relativedelta

from jetstream.model.model import Model
from jetstream.model.analysis import Analysis
from dask.distributed import Client

def get_logger(log_level):
    ch = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(' - '.join(
        ["%(asctime)s", "%(name)s", "%(levelname)s", "%(message)s"]))
    ch.setFormatter(formatter)
    logger = logging.getLogger(__file__)
    logger.setLevel(log_level)
    ch.setLevel(log_level)
    logger.addHandler(ch)

    return logger


@click.command()
@click.option('--product_path', default='', help='Path to model data')
@click.option('--save_path', default='', help='Path to save output')
@click.option('--time_step', default=5, help='Number of years per file')
@click.option('--start_year', default=2015, help="Start year")
@click.option('--end_year', default=2100, help="End year")
@click.option('--model', is_flag=True, help='Run Model instead of Analysis')
@click.option('--log_level', default='INFO')
def cli(product_path,
        save_path,
        time_step,
        start_year,
        end_year,
        model,
        log_level):
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
    logger = get_logger(log_level)

    logger.info(f'Initializing t prime calculation')
    for year in range(start_year, end_year, time_step):
        # Define time ranges 
        start_year = datetime(year, 12, 1).strftime('%Y-%m-%d')
        end_year = datetime(year + time_step, 3, 1).strftime('%Y-%m-%d')
        subset_data = {'time': slice(start_year, end_year), 'lat': 20}

        logger.info(f"Start processing -- {start_year} to {end_year}")

        if model:
            model_object = Model(
                path_to_files=product_path,
                path_to_save_files=save_path,
                subset_dict=subset_data,
                season='DJF',
                temp_interval_size=1,
                chunks={'time': 1},
                rescale_longitude=True
            )
        else:
            model_object = Analysis(
                path_to_files=product_path,
                path_to_save_files=save_path,
                subset_dict=subset_data,
                season='DJF',
                temp_interval_size=1,
                chunks={'time': 1},
                rescale_longitude=True
            )

        model_object.pipeline_methods

if __name__ == '__main__':
    #path_to_scheduler = os.path.join(os.getenv('SCRATCH'),
    #                             'scheduler.json')
    #client = Client(scheduler_file=path_to_scheduler)
    client = Client()
    cli()

