"""
Basic I/O functions to load/unload xarray data from reanalysis
"""

import os
import dask
import xarray as xr
import pandas as pd
from pathlib import Path


def preprocesser(ds,
                 freq='12H',
                 winter=True,
                 start_date=None,
                 end_date=None):

    """
    Pre-processing file mapped to all files pasaed to the reader-n-cutter
    function. 

    This pre-processing function mainly takes care of the dates within the
    files. Ideally, the user will pass a date boundary so files can be
    subsetted in the time dimension (index). 
    """

    ds = ds.sortby('time')

    if winter is True:
        years_in_array = pd.DatetimeIndex(ds.time.values).year.unique().sort_values()

        if len(years_in_array) == 2:
            date_array = pd.date_range(f'{years_in_array[0]}-12-01',
                                      f'{years_in_array[1]}-03-01',
                                      freq=freq)
            ds_subset = ds.where(
                ds.time.isin(date_array), drop=True)

        else:
            raise ValueError(f'{years_in_array} are more than the desired years')

    else:
        date_array =  pd.daate_range(start_date, end_date, freq=freq)

        ds_subset = ds.where(
                ds.time.isin(date_array), drop=True)

    return ds_subset


def model_reader_cutter(path_to_file,
                       spatial_selection):

    # Check files and set I/O
    if isinstance(path_to_file, list):
        nc_files_list = [xr.load_dataset(path) for path in path_to_file]
        nc_files = xr.auto_combine(nc_files_list, concat_dim='time')
    elif isinstance(path_to_file, str) and regex is True:
        nc_files = xr.open_mfdataset(path_to_file, 
                                     combine='by_coords',
                                     parallel=True,
                                     preprocess=preprocesser)
    else:
        nc_files = xr.open_dataset(path_to_file)

    # Set coordinate names
    pass



def era5_reader_n_cutter(path_to_file,
                         spatial_selection,
                         resample_window,
                         save_local=False,
                         regex=True):
    """
    Read file and process to desired location and date. 


    The reader_n_cutter function process one NetCDF datafile and cut it in both
    space and time to obtain a downsample version in a readable format. The
    user can output the output as a planar file (CSV) or as a xarray database
    or array. All operations within this function are just generalizations of
    the xarray classes. 
    """

    if isinstance(path_to_file, list):
        nc_files_list = [xr.load_dataset(path) for path in path_to_file]
        nc_files = xr.auto_combine(nc_files_list, concat_dim='time')
    elif isinstance(path_to_file, str) and regex is True:
        nc_files = xr.open_mfdataset(path_to_file, 
                                     combine='by_coords',
                                     parallel=True,
                                     preprocess=preprocesser)
    else:
        nc_files = xr.open_dataset(path_to_file)

    # xarray does not takes string keys for indexing (see Indexing docs)
    # we're hardcoding dimensions here, but at least we can check them.

    ds_dims = set(list(nc_files.dims.keys()))
    if ds_dims == set(['latitude', 'longitude', 'time']):

        if spatial_selection is not None:
            if len(spatial_selection) == 1:
                nc_files_space_filter = nc_files.where(nc_files.latitude >
                                                       spatial_selection[0],
                                                       drop=True)

                filename = f'df_lat_{spatial_selection[0]}_lon_{spatial_selection[0]}_{resample_window}'

            elif len(spatial_selection) == 2:
                nc_files_space_filter = nc_files.where( 
                    (nc_files.latitude > spatial_selection[0]) &
                    (nc_files.longitude > spatial_selection[1]),
                    drop=True
                )

                filename = f'df_lat_{spatial_selection[0]}_lon_{spatial_selection[0]}_{resample_window}'

            else:
                raise ValueError(f'{spatial_selection} has the wrong length.')
        else:
            nc_files_space_filter = nc_files

        # Resampling using pandas resampling grammar
        resample_filter = nc_files_space_filter.sortby('time').resample(time=resample_window).mean()
        resample_filter = resample_filter.dropna(dim='time')

        if isinstance(path_to_file, Path):
            filename = f'{path_to_file.stem}_resample'
        if save_local == 'csv':
            ds_df = resample_filter.to_dataframe().reset_index(drop=False)
            ds_df.to_csv(f'{filename}.csv', index=False)
        elif save_local == 'netcdf':
            resample_filter.to_netcdf(f'{filename}.nc')
        else:
            return resample_filter
    else:
        raise ValueError(
            (f"['latitude', 'longitude','time'] are the default dims, "
             f"but the Database dims are: {ds_dims}"
            )
        )


