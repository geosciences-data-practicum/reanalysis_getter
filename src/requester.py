"""
Functions to download data systematically from the CDS API

These functions are centered around the ERA-5 reanalysis products and are based
on the cdsapi library. 
"""

import os
import cdsapi
from datetime import datetime

from src.utils import day_hours

def build_request_dics(start_date,
                       end_date,
                       variables_of_interest,
                       subday_frequency = 'hourly',
                       pressure_levels = 'sfc'):
    '''
    Build requests dictionaries for each combination of date/product/level

    This function takes two timestamps to call all required datasets between
    their time range. The dictionaries are stored as a list-array to be used by
    the cdsapi requester. For now the function will download all 24-hr data if
    available
    '''

    time_param = f'{start_date.strftime("%Y-%m-%d")}/to/{end_date.strftime("%Y-%m-%d")}'

    if subday_frequency == 'hourly':
        time = '/'.join(day_hours())
    else:
        time = f'00/to/23/by/{subday_frequency}'

    if not isinstance(pressure_levels, list):
        pressure_levels = [pressure_levels]

        if len(pressure_levels) == 1:
            pressure_param = str(pressure_levels[0])
        else:
            pressure_param = '/'.join(pressure_levels)

    else:
        if len(pressure_levels) == 1:
            pressure_param = str(pressure_levels[0])
        else:
            pressure_param = '/'.join(pressure_levels)


    if not isinstance(variables_of_interest, list):
        variables_of_interest = [variables_of_interest]

        if len(variables_of_interest) == 1:
            variable_param = str(variables_of_interest[0])
        else:
            variable_param = '/'.join(variables_of_interest)

    else:
        if len(variables_of_interest) == 1:
            variable_param = str(variables_of_interest[0])
        else:
            variable_param = '/'.join(variables_of_interest)

    if pressure_levels == 'sfc':
        dict_request = {
            'class': 'ea',
            'date': time_param,
            'expver': '1',
            'levtype': 'sfc',
            'param': variable_param,
            'stream': 'oper',
            'time': time,
            'type': 'an'
        }
    else: 
        dict_request = {
            'class': 'ea',
            'date': time_param,
            'expver': '1',
            'levtype': pressure_param,
            'param': variable_param,
            'stream': 'oper',
            'time': time,
            'type': 'an'
        }

    return(dict_request)


def request_wrapper(file_name, 
                    queue = False,
                    **kwargs):
    """
    Make request to ECMWF API. 


    This function is a mere wrapper of the cdsapi.retrieve method. The wrapper
    will create the API client using the credentials stored in the ~/.cdsapirc
    file (API key and URL). The function will call retrieve data either to the
    server queue, or save the data locally if possible to the path defined by
    file_name. 
    """

    if isinstance(file_name, str) and not '.grb' in file_name:
        Warning(f'file_name has no GRIB extension. By default, all files are GRIB')

    if file_name is None:
        file_name = f'reanalysis_era5_request_{"-".join(kwargs["variables_of_interest"])}_{kwargs["start_date"]}.grib'

    if not os.path.exists('cdsapi_requested_files'):
        os.mkdir('cdsapi_requested_files')

    grib_file_path = os.path.join('cdsapi_requested_files', file_name)

    c = cdsapi.Client()

    dict_params = build_request_dics(start_date = kwargs['start_date'],
                                     end_date = kwargs['end_date'],
                                     variables_of_interest = kwargs['variables_of_interest'],
                                     day_frequency = kwargs['day_frequency'],
                                     pressure_levels = kwargs ['pressure_levels']
                                    )

    if queue is False:
        c.retrieve('reanalysis-era5-complete', dict_params, grib_file_path)
    else:
        c.retrieve('reanalysis-era5-complete', dict_params)


