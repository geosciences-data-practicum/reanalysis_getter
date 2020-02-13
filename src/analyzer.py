"""
Basic I/O functions to load/unload xarray data from reanalysis
"""



import os
import xarray as xr
import pandas as pd
from pathlib import Path


def reader_n_cutter(path_to_file,
                   time_aggregation,
                   time_selection,
                   spatial_selection,
                   resample_window,
                   csv=False,
                   regex=False):
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
        nc_files = xr.open_mfdataset(path_to_file, concat_dim='time')
    else:
        nc_files = xr.open_dataset(path_to_file)

    # xarray does not takes string keys for indexing (see Indexing docs)
    # we're hardcoding dimensions here, but at least we can check them.
 
    ds_dims = set(list(test_ds.dims.keys()))
    if ds_dims == set(['latitude', 'longitude', 'time']):

        if spatial_selection is not None:
            if len(spatial_selection) == 1:
                nc_files_space_filter = nc_files.where(nc_files.latitude >
                                                       spatial_selection[0],
                                                       drop=True)
            elif len(spatial_selection) == 2:
                nc_files_space_filter = nc_files.where( 
                    (nc_files.latitude > spatial_selection[0]) &
                    (nc_files.longitude > spatial_selection[1]),
                    drop=True
                )
            else:
                raise ValueError(f'{spatial_selection} has the wrong length.')
        else:
            nc_files_space_filter = nc_files

        if time_selection is not None:
            if len(time_selection) == 1:
                time_space_filter = nc_files_space_filter.sel(time=time_selection[0])
            if len(time_selection) > 1:
                try:
                    time_space_filter = nc_files_space_filter.where(
                        nc_files_space_filter.time.isin(time_selection),
                        drop=True
                )
                except Exception as e:
                    raise ValueError(
                        (f"Couldn''t slice on time. Check data"
                         f"formats: {e}")
                    )
    else:
        raise ValueError(
            (f"['latitude', 'longitude','time'] are the default dims, "
             f"but the Database dims are: {ds_dims}"
            )


