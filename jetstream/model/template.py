import os
import sys
import dask
import pathlib
import xarray as xr
import numpy as np
import pandas as pd
import bottleneck as bn
from datetime import datetime
from dask.diagnostics import ProgressBar
from descriptors import cachedproperty
from distributed.client import _get_global_client
from abc import ABC, abstractmethod

class Template(ABC):
    """ Abstract class to process and calculate metrics in climate data products

    This class contains a define a pipeline and different methods needed to
    calculate the following metrics using surface temperature data:
     - effective_latitude
     - t_reference
     - t_prime
     Different data classes can be adapted using this class as a template. 
    """

    DIMS = ['time', 'lat', 'lon']
    R_EARTH = 6367.47
    temp_var = ''

    def __init__(self,
                 path_to_files,
                 subset_dict=None,
                 path_to_save_files=None,
                 temp_interval_size=2,
                 moving_window_size=None,
                 season=None,
                 rescale_longitude=False,
                 chunks={'time': 10}):
        self.path_to_files = path_to_files
        self.path_to_save = path_to_save_files
        self.temp_interval_size = temp_interval_size
        self.moving_window_size = moving_window_size
        self.season = season
        self.rescale_longitude = rescale_longitude
        self.subset_dict = subset_dict
        self.chunks = chunks

        if isinstance(self.path_to_files, pathlib.Path):
            self.product = self.path_to_files.stem
        else:
            self.product = pathlib.Path(self.path_to_files).stem

    def __repr__(self):
        return f'''
               Climate product: {self.product} \n
               Grid size: ({self.lat_grid_size}, {self.lon_grid_size})
               '''

    @cachedproperty
    def pipeline_methods(self):

        dir_save = self.build_save_dirs()

        if self.subset_dict is not None:
            time_slice = self.subset_dict['time']
            filename_tref = f'{self.product}_t_prime_{time_slice.start}_{time_slice.stop}.nc4'
            filename_eff_lat = f'{self.product}_eff_lat_{time_slice.start}_{time_slice.stop}.nc4'
        else:
            filename_tref = f'{self.product}_t_prime.nc4'
            filename_eff_lat = f'{self.product}_eff_lat.nc4'

        self.t_prime_calculation.to_netcdf(os.path.join(dir_save, filename_tref))
        self.effective_latitude_xr.to_netcdf(os.path.join(dir_save,filename_eff_lat))

    @property
    def data_array(self) -> xr.Dataset:
        """ Lazy load model/analysis data into memory and subsetting raw data
        using `self.subset_dict`

        This function cuts the raw array object and makes a series of
        transformations to facilitate the data assimilation process. This
        function names coordinates to common dimnesions, and then cut the data
        if a dict is passed to the class. It also re-scales longitude, which
        comes in 0 to 360 on must of climate products.
        """

        xr_data = xr.open_mfdataset(self.path_to_files,
                                   chunks=self.chunks,
                                    parallel=True)

        if not all(x in list(xr_data.coords) for x in self.DIMS):
            xr_data = xr_data.rename({
                'latitude': 'lat',
                'longitude': 'lon',
            })

        if self.subset_dict is not None:
            print(f'Cutting data using {self.subset_dict}')
            xr_data = self.cut(xr_data)

        if self.season is not None:
            xr_data = xr_data.where(xr_data.time.dt.season == self.season,
                                    drop=True)

        if self.rescale_longitude is True:
            xr_data = xr_data.assign_coords(lon=(((xr_data.lon + 180) % 360) -
                                                 180)).sortby('lon')

        return xr_data

    @property
    def data_array_dask_df(self):
        """ Return data array as dask DataFrame and calculate temperature bins.

        Thins property will yield a dask.dataframe that contain the
        `self.data_array` data with the temperature bining and latitudinal grid
        areas per each row. The bining can be either daily, by default, or use
        a window set by `self.moving_window_size`. This process is right now
        not very optimized, so it might take a while to process in large
        datasets.

        Returns:
            dask.datarame.DaskDataFrame
        """

        # Metadata for group by operation in dask.dd.groupby
        meta = pd.DataFrame({
            'time': pd.Series([], dtype='<M8[ns]'),
            'lat': pd.Series([], dtype='float'),
            'lon': pd.Series([], dtype='float'),
            't2m': pd.Series([], dtype='float'),
            'area_grid': pd.Series([], dtype='float'),
            'temp_bucket': pd.Series([], dtype='float'),
        })

        self.data_array['area_grid'] = self._calculate_area_from_latitude(
            self.data_array.lat
        )

        # Calculate window operation if selected
        if self.moving_window_size is not None:
            if isinstance(self.moving_window_size, int):
                window_array = (
                    self.data_array[self.temp_var].
                    rolling(time=self.moving_window_size,
                            center=False,
                            min_periods=self.moving_window_size
                            )
                )
            else:
                raise NotImplementedError

            window_arrays = []
            for label, array_window in window_array:
                bucket_array = self._create_bucket_window(
                    w_arr=array_window,
                    label_time=label)
                window_arrays.append(bucket_array)

            lazy_results = dask.compute(*window_arrays[self.moving_window_size:])
            lazy_results_no_none = [r for r in lazy_results if r is not None]

            self.data_array['temp_bucket'] = xr.concat(lazy_results_no_none,
                                                       dim='time')

            #return unified chunks since window changed chunks
            return (
                self.data_array
                .unify_chunks()
                .to_dask_dataframe(dim_order=self.DIMS)
            )

        else:
            # Yield dask.dataframe and process groupby operation
            array_ddf = self.data_array.to_dask_dataframe(dim_order=self.DIMS)
            array_ddf_transform = (
                array_ddf
                .groupby(['time'])
                .apply(self._bucket_builder_ddf,
                       meta=meta)
            )

            return array_ddf_transform

    @abstractmethod
    def cut(self, array_obj):
        """ Wrapper function to slice xarray using a dictionary

        Args:
        xr_array (xr.DataArray or xr.Dataset)

        returns: xr.Dataset or xr.Dataarray
        """

        pass

    @cachedproperty
    def lat_grid_size(self):
        """ Calculate grid size from model/analysis
        """
        lat_diff = np.unique(np.diff(self.data_array.lat))

        if len(lat_diff) != 1:
            lat_diff = np.mean(lat_diff)

        return np.abs(lat_diff)

    @cachedproperty
    def lon_grid_size(self):
        """ Calculate grid size from model/analysis
        """
        lon_diff = np.unique(np.diff(self.data_array.lon))

        if len(lon_diff) != 1:
            lon_diff = np.mean(lon_diff)
        return np.abs(lat_diff)

    @cachedproperty
    def lon_grid_size(self):
        """ Calculate grid size from model/analysis
        """
        lon_diff = np.unique(np.diff(self.data_array.lon))

        if len(lon_diff) != 1:
            lon_diff = np.mean(lon_diff)

        return np.abs(lon_diff)

    def _distributions_lat_eff(self, cdf_areas):
        """ Calculate cumulative distribution of effective latitudes (phi-effective)

        This is an intermediate step to calculate both Tref and T_prime.

        Parameteres:
        - cdf_areas (np.array or pd.Series) Cumulative area in squared
          kilometers (km^2).

        Returns: np.array with cumulative effective latitudes organized by
        temperature bucket. 
        """

        pdf_lat_effs = np.pi / 2. - np.arccos(1 - cdf_areas /
                                              (2 * np.pi * self.R_EARTH**2))
        pdf_lat_effs_deg = np.rad2deg(pdf_lat_effs)

        return pdf_lat_effs_deg

    def _calculate_area_from_latitude(self, latitude):
        """
        Calculate area using latitude 

        Parameters
        ----------
            - latitude (int): latitude

        Returns
        -------
            Area per grid
        """
        DPHI = self.lat_grid_size * np.pi / 180.0
        DLAMBDA = self.lon_grid_size * np.pi / 180.0

        return ((self.R_EARTH)**2 * np.cos(np.deg2rad(latitude)) * DPHI *
                DLAMBDA)

    def _bucket_builder_ddf(self, ddf):
        """ Build temperature buckets using max and min in dataframe
        """

        bins_left = np.vectorize(lambda x: x.left)
        min_val = np.floor(ddf[self.temp_var].min())
        max_val = np.ceil(ddf[self.temp_var].max())
        offset_scale = max_val + 2

        buckets = np.arange(min_val,
                            max_val + offset_scale,
                            self.temp_interval_size)

        bin_array = pd.cut(ddf[self.temp_var], 
                           bins=buckets, 
                           precision=0,
                           include_lowest=True)

        df_ = pd.DataFrame({
            'time': ddf.time,
            'lat': ddf.lat,
            'lon': ddf.lon,
            self.temp_var: ddf[self.temp_var],
            'area_grid': ddf.area_grid,
            'temp_bucket': bins_left(bin_array)
        })

        return df_

    @dask.delayed
    def _create_bucket_window(self, w_arr, label_time):
        ''' Lazy Build temperature buckets in a rolling xarray object

        Parameters:
        ----------
        - w_arr (xr.DataArray.rolling): A rolling object with the defined window
          to calculate buckets
        - label_time (pd.Timedelta or pd.datetime): A timestamp to identify the
          start of the window. Usually, the `xr.DataArray.rolling` includes
          labels per each start of the window if `center=False`.

        Returns:
            dask.future
        '''

        # calculate min and max for the aray_window
        max_temp = np.ceil(w_arr.max().values)
        min_temp = np.floor(w_arr.min().values)
        label_str = pd.to_datetime(label_time.values).strftime('%Y-%m-%d')

        if not any(np.isnan([max_temp, min_temp])):
            bins = np.arange(min_temp,
                             max_temp,
                             self.temp_interval_size)
            bins_left_labels = dict(enumerate(bins, 0))

            buckets = np.digitize(w_arr.sel(time=label_str),
                                  bins=bins)
            buckets_w_labels = np.vectorize(bins_left_labels.get)(buckets)
            buckets_arr = xr.DataArray(buckets_w_labels.squeeze(),
                                       coords=[
                                           ('lat', w_arr.lat),
                                           ('lon', w_arr.lon)
                                       ]).astype(np.float64)
            buckets_arr = buckets_arr.assign_coords({'time': label_time})
        else:
            buckets_arr = None

        return buckets_arr

    @cachedproperty
    def grid_area_xr(self):
        """ Cumulative area calculation per temperature bin and date

        This functions takes a dask.DataFrame and calculates the cumulative
        area per temperature bin, defined by the cut_interval option, and
        grouped by date. The function uses Dask objects and returns a computed
        pd.DataFrame.

        Returns: xr.DataArray with cumulative area maps per time.
        """

        dd_data_group = (
            self.data_array_dask_df
            .reset_index(drop=True)
            .groupby(['temp_bucket', 'time'])
            .area_grid
            .sum()
        ).compute()

        # Cumumlative sum
        dd_data_group_time = (
            dd_data_group
            .sort_index()
            .groupby(level=[1])
            .cumsum()
            .reset_index()
        )

        # Calculate effective latitudes by using the temperature area weights
        dd_data_group_time['cdf_eff_lat_deg'] = (
            dd_data_group_time
            .groupby('time')
            .area_grid
            .apply(self._distributions_lat_eff)
        )

        dd_group_time_array = (
            dd_data_group_time
            .set_index(['time', 'temp_bucket'])
            .to_xarray()
        )
        dd_group_time_array_delayed = dd_group_time_array.chunk(self.chunks)

        return  dd_group_time_array_delayed

    @cachedproperty
    def effective_latitude_xr(self):
        """ DataArray with effective latitude
        """

        grid_areas_ddf = self.grid_area_xr.to_dataframe().reset_index()
        grid_areas_ddf = grid_areas_ddf[
            ['temp_bucket', 'cdf_eff_lat_deg', 'time']
        ]

        merge_ddf = (
            self.data_array_dask_df
            .reset_index(drop=True)
            #.repartition(npartitions=100)
            .merge(grid_areas_ddf,
                   on=['time', 'temp_bucket'],
                   how='left')
        )

        eff_lat_xr = self.dask_data_to_xarray(merge_ddf,
                                              var='cdf_eff_lat_deg')

        eff_lat_xr.name = 'effective_latitude'

        return eff_lat_xr

    def vectorized_temp_ref(self, cdf_eff_lat, latitudes, temp_bin_edges):
        """
        Latitudinal reference temperature to capture the gradient effect of the
        jet-stream (t_ref)

        Using the cumulative effective latitude map, temp_ref is the interpolation
        of the effective latitudes given a temperature bucket. An interpolation is
        made per each latitude.

       Parameters:
           - cdf_lat_effs (np.nd-array)
           - temp_binedges (str): column name with the temperature bin. We use
           'temp_brackets'.
           - pdf_lat_effs (str): column name with the name of the cumulative
           effective latitudes.

        Returns: An ndarray with the interpolated values.
        """

        xp = cdf_eff_lat[ ~ np.isnan(cdf_eff_lat)]
        fp = temp_bin_edges[ ~ np.isnan(cdf_eff_lat)]
        t_ref = np.interp(latitudes,
                          np.flip(xp),
                          np.flip(fp))

        return t_ref

    @cachedproperty
    def t_prime_calculation(self):
        """ Jet-stream metric
        return: A delayed dask.DataFrame with the t-prime, t-ref. 
        """

        t_ref = np.apply_along_axis(self.vectorized_temp_ref,
                                    axis=1,
                                    arr=self.grid_area_xr.cdf_eff_lat_deg,
                                    temp_bin_edges=self.grid_area_xr.temp_bucket,
                                    latitudes=self.data_array.lat.values)

        t_ref_arr = xr.DataArray(t_ref,
                                 coords=[
                                     ('time', self.grid_area_xr.time.values), 
                                     ('lat', self.data_array.lat.values)
                                 ])


        t_combined = t_ref_arr.\
            combine_first(self.data_array[self.temp_var]).\
            to_dataset(name = 't_ref')

        t_combined[self.temp_var] = self.data_array[self.temp_var]
        t_combined['t_prime'] = t_combined[self.temp_var] - t_combined['t_ref']

        return t_combined

    def dask_data_to_xarray(self, df, var=None):
        """
        Transform delayed dask.DataFrame to xarray object

        Import Dask dataframes to xarrays is not easy job with large data frames.
        This function takes a delayed dask data frame and calculates the right
        shape to create a Dask DataFrame. 

        Parameters:
            - df (dask.DataFrame): a delayed Dask dataframe.

        Return: xarray Dataset
        """

        lazy_values = [dask.delayed(df[dim].unique()) for dim in self.DIMS]
        dims_values = [future for future in dask.compute(*lazy_values)]
        shape = tuple([len(x) for x in dims_values])

        var_array = df[var].values
        var_array.compute_chunk_sizes()
        var_array_reshape = var_array.reshape(shape)
        tuple_data = (self.DIMS, var_array_reshape)

        coords_dict = dict(zip(self.DIMS, dims_values))
        #values_dicts = dict(zip(extract_vars, values_arrays))

        xarr = xr.DataArray(var_array_reshape, 
                            coords=dims_values,
                            dims=self.DIMS)

        return xarr.sortby(['lat', 'lon'])

    def build_save_dirs(self):
        if self.path_to_save is not None:
            product_dir = os.path.join(self.path_to_save, self.product)
            if not os.path.exists(product_dir):
                os.mkdir(product_dir)

        return product_dir
