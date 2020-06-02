"""
Jet-stream methods
"""

import os
import dask
import numpy as np
import xarray as xr
import pandas as pd
import seaborn as sns
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
from pathlib import Path


def calculate_area_from_latitude(latitude,
                                grid_lon=None,
                                grid_lat=None):
    """
    Calculate area using latitude 

    Parameters:
        - latitude (int): latitude

    Returns: Area per grid
    """

    R_EARTH = 6367.47

    if grid_lon is None and grid_lat is None:
        DPHI = 0.25*np.pi/180.0
        DLAMBDA=0.25*np.pi/180.0
    else:
        DPHI = grid_lat*np.pi/180.0
        DLAMBDA=grid_lon*np.pi/180.0

    return (R_EARTH)**2 * np.cos(np.deg2rad(latitude)) * DPHI * DLAMBDA


def area_calculation_real_area(dd_data,
                               cut_interval,
                               grid_lat=0.25,
                               grid_lon=0.25,
                               resample_time = False,
                               grouping_time_interval='1w',
                               temp_var='t2m'):
    """
    Cumulative area calculation per temperature bin and date

    This functions takes a dask.DataFrame and calculates the cumulative area
    per temperature bin, defined by the cut_interval option, and grouped by
    date. The function uses Dask objects and returns a computed pd.DataFrame.  

    Parameters:
        - dd_data (dask.DataFrame): Dask dataframe with partitioned data by
        time.
        - cut_interval (int): Temperature bins size.
        - resample_time (bool): Resampling time to create grouped area maps.
        Default is False. Thus, it will create an area map per each time in the
        dd_data.
        - grouping_time_interval (str): If resample_time is True, define the
        time window for grouping. Default is one week: '1w'
        - temp_var (str): variable to calculate buckets. Default is 't2m'.

    Returns: pd.DataFrame with cumulative area maps per time.
    """

    dd_data['area_grid'] = dd_data.latitude.map_partitions(
        calculate_area_from_latitude,
        grid_lat=grid_lat,
        grid_lon=grid_lon
    )

    # Remove all areas equal to 0
    #dd_data = dd_data[dd_data.area_grid > 0]

    if not 'temp_brakets' in dd_data.columns:
        t_max, t_min = dask.compute(dd_data[temp_var].max(), dd_data[temp_var].min())
        range_cuts = np.arange(t_min, t_max , cut_interval)

        dd_data['temp_bracket'] = dd_data[temp_var].map_partitions(
            pd.cut, range_cuts
        )

    # Grouper by time: 
    if resample_time:
        group_time = pd.Grouper(key='time', 
                                freq=grouping_time_interval)
        dd_data_group = dd_data.groupby(['temp_bracket', group_time])
    else:
        dd_data_group = dd_data.groupby(['temp_bracket', 'time'])

    # Group by data
    dd_data_group = dd_data_group.\
    area_grid.\
    sum().\
    compute()

    #Cumumlative sum
    dd_data_group_time = dd_data_group.groupby(level=[1]).cumsum()

    return dd_data_group_time


def dists_of_lat_eff(cdf_areas):
    """
    Calculate cumulative distribution of effective latitudes (phi-effective)

    This is an intermediate step to calculate both Tref and T_prime.

    Parameteres:
        - cdf_areas (np.array or pd.Series) Cumulative area.

    Returns: np.array with cumulative effective latitudes organized by
    temperature bucket. 
    """

    R_EARTH = 6367.47 

    pdf_lat_effs = np.pi/2.-np.arccos(1-cdf_areas / (2*np.pi*R_EARTH**2))
    pdf_lat_effs_deg = np.rad2deg(pdf_lat_effs)

    return pdf_lat_effs


def temp_ref(ddf,
             area_weights,
             temp_binedges,
             pdf_lat_effs,
             resample_time=False):
    """
    Latitudinal reference temperature to capture the gradient effect of the
    jet-stream (t_ref) 

   Using the cumulative effective latitude map, temp_ref is the interpolation
   of the effective latitudes given a temperature bucket. An interpolation is
   made per each latitude.

   Parameters:
       - dff (dask.DataFrame): A raw data dask DataFrame 
       - area_weights (pd.DataFrame): A data frame with cumulative area mapping
       for each date and bucket. This is the output of
       area_calculation_real_area.
       - temp_binedges (str): column name with the temperature bin. We use
       'temp_brackets'. 
       - pdf_lat_effs (str): column name with the name of the cumulative
       effective latitudes. 

    Returns: An ndarray with the interpolated values. 
    """
 
    # Avoid problems with merge
    ddf['temp_bracket'] = ddf.temp_bracket.apply(lambda x: x.left.astype(float))

    if resample_time:
        area_weights['week_year']  = area_weights.time.dt.strftime('%Y-%W')
        ddf['week_year']  = ddf.time.dt.strftime('%Y-%W')
        ddf_merge = ddf.merge(area_weights,
                              on=['week_year', 'temp_bracket'],
                              how='left')
    else:
        ddf_merge = ddf.merge(area_weights,
                              on=['time', 'temp_bracket'],
                             how='left')
 
    # Interpolate to calculate the t_ref latitde mapping
    t_ref =  np.interp(ddf_merge.latitude,
                       np.flip(ddf_merge[pdf_lat_effs]),
                       np.flip(ddf_merge[temp_binedges])
                      )


    return t_ref


def t_prime_calculation(dd_data, 
                        temp_var='t2m',
                        resample_time=False,
                        grouping_time_interval='2w',
                        build_buckets=True,
                        cut_interval=2,
                        grid_lat=0.25,
                        grid_lon=0.25,
                        all_series=True,
                        max_min=None):
    """
    Jet-stream metric

    A better description here is needed! 

    Parameters:
        - temp_var (str): name of surface_temperature value
        - resample_time (bool): time resampling to calculate cumulative areas
        per latitude. 
        - grouping_time_interval (str): If resample_time is True, which
        grouping window should be used. Default is two weeks: '2w'.
        - build_buckets (bool): If no buckets are defined, create buckets
        using the cutting_interval. -deprecated-
        - cut_interval (int): temperature size bin. 
        - all_series (bool): If True, use the whole series maximum and minimum
        to calculate buckets. If false, define a max_min. Defualt is True. 
        - max_min (tuple): A tuple with (temp_max, temp_min).

    Return: A delayed dask.DataFrame with the t-prime, t-ref. 
    """

    # Calculate binned temperature using all series min, max
    if all_series:
        t_max, t_min = dask.compute(dd_data[temp_var].max(), dd_data[temp_var].min())
        range_cuts = np.arange(t_min, t_max, cut_interval)
    else:
        t_max, t_min = max_min
        range_cuts = np.arange(t_min, t_max, cut_interval)

    # Calculate temperature brackets
    dd_data['temp_bracket'] = dd_data[temp_var].map_partitions(
        pd.cut, range_cuts
    )

    # Calculate area weights
    area_weights = area_calculation_real_area(dd_data=dd_data,
                                              grid_lat=grid_lat,
                                              grid_lon=grid_lon,
                                              resample_time=resample_time,
                                              cut_interval=cut_interval,
                                              grouping_time_interval='1w')

    # Calculate effective latitudes by using the temperature area weights
    area_weights = area_weights.reset_index(drop=False)

    area_weights['cdf_eff_lat_mapping'] = area_weights.groupby('time').\
    area_grid.apply(lambda x: dists_of_lat_eff(x))

    #area_weights = area_weights[ ~ area_weights.cdf_eff_lat_mapping.isna()]
    area_weights['temp_bracket'] = area_weights.temp_bracket.apply(lambda x: x.left.astype(float)).astype(float)
    area_weights['eff_lat_deg'] = np.rad2deg(area_weights.cdf_eff_lat_mapping)

    # Merge and calculate t_ref by time partition
    test_p = dd_data.groupby(['time']).apply(temp_ref,
                                             area_weights=area_weights,
                                             resample_time=resample_time,
                                             temp_binedges='temp_bracket',
                                             pdf_lat_effs='eff_lat_deg')

    # Assign temperature referece to main dataframe and calculate t_prime
    t_ref = test_p.compute()
    t_ref.index = t_ref.index.astype(str)
    values = np.array(t_ref.tolist())
    new_index = np.repeat(t_ref.index, values.shape[1])

    t_ref_df = pd.Series(values.ravel(), index=new_index)
    t_ref_df_noidx = t_ref_df.reset_index(drop=True)

    dd_data['tref'] = t_ref_df_noidx
    dd_data['t_prime'] = dd_data['t2m'] - dd_data['tref']

    return dd_data


def dask_data_to_xarray(df,
                        dims,
                        shape=None,
                        path=None,
                        target_variable='t2m'):
    """
    Transform delayed dask.DataFrame to xarray object

    Import Dask dataframes to xarrays is not easy job with large data frames.
    This function takes a delayed dask data frame and calculates the right
    shape to create a Dask DataFrame. 

    Parameters:
        - df (dask.DataFrame): a delayed Dask dataframe.
        - dims (list): list of column names with the array dimensions. Usually
        time, lat and lon. 
        - shape (tuple): shape of xarray. If None, the function will calculate
        the shape with the dimension sizes. Default is None. 
        - path (str): Path to save file. Default is None.
        - target_variable: variable(s) to include in the xarray.

    Return: xarray Dataset
    """

    var_array = df[target_variable].values
    var_array.compute_chunk_sizes()

    if shape is None:
        shape = tuple([len(df[dim].unique()) for dim in dims])

    var_array_reshape = var_array.reshape(shape)

    dims_values = [df[dim].unique() for dim in dims]
    coords_dict = dict(zip(dims, dims_values))

    xarr = xr.DataArray(var_array_reshape.compute(),
                        dims = dims,
                        coords = coords_dict
                       )
    return xarr



