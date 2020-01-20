"""
Functions to download data systematically from the CDS API

These functions are centered around the ERA-5 reanalysis products and are based
on the cdsapi library. 
"""

import cdsapi


from src.utils import datetime_range

def build_request_dics(start_date,
                       end_date,
                       presure_levels,
                       variables_of_interest
                      ):
    '''
    Build requests dictionaries for each combination of date/product/level

    This function takes two timestamps to call all required datasets between
    their time range. The dictionaries are stored as a list-array to be used by
    the cdsapi requester. For now the function will download all 24-hr data if
    available
    '''

    time_param = f'{start_date.strftime("%Y-%m-%d")}/to/{end_date.strftime("%Y-%m-%d")}'
    time = day_hours

    if presure_levels = 'sfc':
        dict_request = {
            'class': 'ea',
            'date': time_param
            'expver': '1',
            'levtype': 'sfc',
            'param': '/'.join(variables_of_interest)
            'stream': 'oper',
            'time': '/'.join(time)
            'type': 'an'
        }
    else: 
        dict_request = {
            'class': 'ea',
            'date': time_param
            'expver': '1',
            'levtype': '/'.join(presure_levels),
            'param': '/'.join(variables_of_interest)
            'stream': 'oper',
            'time': '/'.join(time)
            'type': 'an'
        }











