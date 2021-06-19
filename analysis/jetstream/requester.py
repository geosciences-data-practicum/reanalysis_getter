"""
Functions to download data systematically from the CDS API

These functions are centered around the ERA-5 reanalysis products and are based
on the cdsapi library. 
"""

import os
import cdsapi
import logging
from datetime import datetime

from jetstream.utils import day_hours, date_elements


def build_request_dict(start_date,
                       end_date,
                       variables_of_interest,
                       months=None,
                       years=None,
                       days=None,
                       subday_frequency = 'hourly',
                       pressure_levels = ['sfc']):
    '''
    Build requests dictionaries for each combination of date/product/level

    This function takes two timestamps to call all required datasets between
    their time range. The dictionaries are stored as a list-array to be used by
    the cdsapi requester. For now the function will download all 24-hr data if
    available
    '''

    if start_date is not None and end_date is not  None:
        years, months, days = date_elements(start_date = start_date,
                                            end_date = end_date,
                                            delta={'days': 1})

    if subday_frequency == 'hourly':
        time = day_hours(1)
    else:
        time = day_hours(subday_frequency)

    if not isinstance(pressure_levels, list):
        pressure_levels = [pressure_levels]

    if not isinstance(variables_of_interest, list):
        variables_of_interest = [variables_of_interest]

    if 'sfc' in pressure_levels and len(pressure_levels) == 1:
        dict_request = {
            'product_type': 'reanalysis',
            'format': 'netcdf',
            'variable': variables_of_interest,
            'year': years,
            'month': months,
            'day': days,
            'time': time,
        }
    elif 'sfc' not in pressure_levels: 
        dict_request = {
            'product_type': 'reanalysis',
            'format': 'netcdf',
            'pressure_level': pressure_levels,
            'variable': variables_of_interest,
            'year': years,
            'month': months,
            'day': days,
            'time': time,
        }

    return dict_request


def request_wrapper( path,
                    wait_queue=True,
                    file_name=None,
                    **kwargs):
    """
    Make request to ECMWF API. 

    This function is a mere wrapper of the cdsapi.retrieve method. The wrapper
    will create the API client using the credentials stored in the ~/.cdsapirc
    file (API key and URL). The function will call retrieve data either to the
    server queue, or save the data locally if possible to the path defined by
    file_name. 
    """

    if isinstance(file_name, str) and not '.nc' in file_name:
        Warning(f'file_name has no NetCDF extension. By default, all files are NetCDF (.nc)')

    if file_name is None:
        variable_str = ''.join(kwargs['variables_of_interest'])
        time_str = kwargs['start_date'].strftime("%Y%m")
        file_name = f'reanalysis_era5_request_{variable_str}_{time_str}_{kwargs["subday_frequency"]}.nc'

    if not os.path.exists(os.path.join(path, 'cdsapi_requested_files')):
        os.mkdir(os.path.join(path, 'cdsapi_requested_files'))

    nc_file_path = os.path.join(path, 'cdsapi_requested_files', file_name)

    if not os.path.exists(nc_file_path):

        c = cdsapi.Client()
        dict_params = build_request_dict(start_date = kwargs['start_date'],
                                         end_date = kwargs['end_date'],
                                         variables_of_interest = kwargs['variables_of_interest'],
                                         subday_frequency = kwargs['subday_frequency'],
                                         pressure_levels = kwargs ['pressure_levels']
                                        )

        if 'sfc' in kwargs['pressure_levels']: 
            c.retrieve('reanalysis-era5-single-levels', dict_params, nc_file_path)
        else:
            c.retrieve('reanalysis-era5-pressure-levels', dict_params, nc_file_path)
    else:
        print(f'{nc_file_path} already exists in path') 
