import os
import sys
import dask
import pathlib
import xarray as xr
import numpy as np
import pandas as pd
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

    chunks = {'time': 1}
    DIMS = ['lat', 'lon', 'time']
    R_EARTH = 6367.47

    def __init__(self,
                 path_to_files,
                 subset_dict=None,
                 path_to_save_files=None,
                 temp_interval_size=2,
                 var='t2m'):
        self.path_to_files = path_to_files
        self.path_to_save = path_to_save_files
        self.temp_interval_size = temp_interval_size
        self.var = var
        self.subset_dict=subset_dict
        self.outvars=['t_ref', 't_prime', self.temp_var]

    def __repr__(self):

        if isinstance(self.path_to_files, pathlib.Path):
            product = self.path_to_files.stem
        else:
            product = pathlib.Path(self.path_to_files).stem
        return f'''
               Climate product: {product} \n
               Grid size: ({self.lat_grid_size}, {self.lon_grid_size})
               '''

    def template_methods():
        self.calculate_t_prime()
        self.demean()

    @cachedproperty
    def data_array(self):
        """ Lazy load model/analysis data into memory. 
        """

        client = _get_global_client()
        xr_data = xr.open_mfdataset(self.path_to_files,
                                 chunks=self.chunks,
                                 parallel=True)

        if not all(x in list(xr_data.coords) for x in self.DIMS):
            xr_data = xr_data.rename({
                'latitude': 'lat',
                'longitude': 'lon',
            })

        if self.subset_dict is not None:
            xr_data = self.cut(xr_data)
            print('Cut data')

        return xr_data

    @property
    def data_array_dask_df(self):
        """ Return data array as dask DataFrame
        """
        return self.data_array.to_dask_dataframe(dim_order=['time', 'lat', 'lon'])

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

        return lat_diff

    @cachedproperty
    def lon_grid_size(self):
        """ Calculate grid size from model/analysis
        """
        lon_diff = np.unique(np.diff(self.data_array.lon))

        if len(lon_diff) != 1:
            lon_diff = np.mean(lon_diff)

        return lon_diff


    def _calculate_area_from_latitude(self, latitude):
        """
        Calculate area using latitude 

        Parameters:
            - latitude (int): latitude

        Returns: Area per grid
        """
        DPHI = self.lat_grid_size*np.pi/180.0
        DLAMBDA=self.lon_grid_size*np.pi/180.0

        return (
            (self.R_EARTH)**2 *
            np.cos(np.deg2rad(latitude)) *
            DPHI *
            DLAMBDA
        )

    @property
    def grid_area_df(self):
        """
        Cumulative area calculation per temperature bin and date

        This functions takes a dask.DataFrame and calculates the cumulative area
        per temperature bin, defined by the cut_interval option, and grouped by
        date. The function uses Dask objects and returns a computed pd.DataFrame.  

        Returns: pd.DataFrame with cumulative area maps per time.
        """

        df = self.data_array_dask_df.copy()
        df['area_grid'] = df.lat.map_partitions(
            self._calculate_area_from_latitude
        )

        if not 'temp_brakets' in df.columns:
            t_max, t_min = dask.compute(df[self.temp_var].max(), 
                                        df[self.temp_var].min())
            range_cuts = np.arange(t_min, t_max , self.temp_interval_size)

            df['temp_bracket'] = df[self.temp_var].map_partitions(
                pd.cut, range_cuts
            )

        dd_data_group = df.groupby(['temp_bracket', 'time'])

        # Group by date
        dd_data_group = dd_data_group.\
        area_grid.\
        sum().\
        compute()

        # Cumumlative sum
        dd_data_group_time = dd_data_group.groupby(level=[1]).cumsum()

        return dd_data_group_time

    def _distributions_lat_eff(self, cdf_areas):
        """
        Calculate cumulative distribution of effective latitudes (phi-effective)

        This is an intermediate step to calculate both Tref and T_prime.

        Parameteres:
        - cdf_areas (np.array or pd.Series) Cumulative area.

        Returns: np.array with cumulative effective latitudes organized by
        temperature bucket. 
        """

        client = _get_global_client()

        pdf_lat_effs = np.pi/2.-np.arccos(1-cdf_areas / (2*np.pi*self.R_EARTH**2))
        pdf_lat_effs_deg = np.rad2deg(pdf_lat_effs)

        return pdf_lat_effs

    def _temp_ref(self,
                  ddf,
                  area_weights,
                  temp_binedges,
                  cdf_lat_effs):
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

        # Filter area_weights
        unique_time = ddf.name
        areas_time = area_weights[area_weights['time'] == unique_time]

        # Interpolate to calculate the t_ref latitde mapping
        t_ref = np.interp(ddf.lat.unique(),
                          np.flip(areas_time[cdf_lat_effs]),
                          np.flip(areas_time[temp_binedges])
                          )

        t_ref_df = pd.DataFrame({
            't_ref': t_ref,
            'time': unique_time,
            'lat': ddf.lat.unique()
        })

        return t_ref_df

    @cachedproperty
    def t_prime_calculation(self): 
        """ Jet-stream metric

        return: A delayed dask.DataFrame with the t-prime, t-ref. 
        """

        client = _get_global_client()

        meta = pd.DataFrame([], columns=["t_ref", 'time', 'lat'],
                            index=pd.Index([], name="time"), dtype=str)

        # Calculate effective latitudes by using the temperature area weights
        area_weights = self.grid_area_df.reset_index(drop=False)
        area_weights['cdf_eff_lat_mapping'] = area_weights.groupby('time').\
        area_grid.apply(lambda x: self._distributions_lat_eff(x))

        #area_weights = area_weights[ ~ area_weights.cdf_eff_lat_mapping.isna()]
        area_weights['temp_bracket'] = area_weights.temp_bracket.apply(
            lambda x: x.left.astype(float)).astype(float)
        area_weights['eff_lat_deg'] = np.rad2deg(area_weights.cdf_eff_lat_mapping)

        # Merge and calculate t_ref by time partition
        # Note: dask arrays need metadata on the returning object
        t_ref_lazy = self.data_array_dask_df.groupby(['time']).apply(self._temp_ref,
                                                  area_weights=area_weights,
                                                  temp_binedges='temp_bracket',
                                                  cdf_lat_effs='eff_lat_deg',
                                                  meta=meta
                                                  )

        # Calculate t_refs and then merge with raw data
        with ProgressBar():
            t_ref = t_ref_lazy.compute()

        t_ref_df_noidx = t_ref.reset_index(drop=True)
        merge_data = self.data_array_dask_df.merge(t_ref_df_noidx, 
                                                   on=['time', 'lat'],
                                                   how='inner')
        merge_data['t_prime'] = merge_data[self.temp_var] - merge_data['t_ref']

        # Compute merge dask object and save
        self.dask_data_to_xarray(df=merge_data)

        return merge_data

    @cachedproperty
    def demean(self,
               df):
        """ Demean array results on xarray object

        Demean array values using two main strategies: 
         - take the day of the year mean and calculate anomaly using that mean. 
         - calculate `rolling` window and take within-window mean. Then,
           calculate anomaly using the window mean. 

        Return: xarray Dataset or saved object
        """
        pass

    def dask_data_to_xarray(self,
                            df):
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
            shape = tuple([len(df[dim].unique()) for dim in self.DIMS])

        var_array_reshape = var_array.reshape(shape)

        dims_values = [df[dim].unique() for dim in self.DIMS]
        coords_dict = dict(zip(self.DIMS, dims_values))

        xarr = xr.DataArray(var_array_reshape.compute(),
                            dims = self.DIMS,
                            coords = coords_dict
                           )
        if self.path_to_save_files is not None:
            if isinstance(self.path_to_files, pathlib.Path):
                product = self.path_to_files.stem
            else:
                product = pathlib.Path(self.path_to_files).stem
 
            path_save = os.path.join(self.path_to_save_files,
                                     f'{self.name_ds}_processed.nc4')
            save_array = xarr.to_netcdf(path_save, compute=False)
            with ProgressBar():
                save_array.compute()

        return xarr

