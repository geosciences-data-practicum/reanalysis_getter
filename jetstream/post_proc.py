"""
Post-processing analysis on T_ref and phi_eff to produce pretty plots for diagnostic and publication purposes.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
import pandas as pd
from scipy import fft, fftpack
from scipy.stats import skew
from matplotlib.colors import LogNorm
import joypy
os.environ['PROJ_LIB'] = '/home/afarah/.conda/envs/jetstream/share/proj/'
import cartopy.crs as ccrs
from descriptors import cachedproperty
from distributed.client import _get_global_client

class SingleModelPostProcessor(object):
    """ Post-processing routines for analysis of climate models and reanalysis
    with T-prime, effective latitude and surface temperature data
    """

    def __init__(self,
                 path_to_files,
                 chunks={'time': 1},
                 path_to_save_files=None,
                 diagnostic_var='t_prime',
                 season='DJF'):
        self.chunks = chunks
        self.path_to_files = path_to_files
        self.path_to_save = path_to_save_files
        self.season = season
        self.var = diagnostic_var

    def sel_winters(self,start_year=2015,end_year=2100):
        winters = pd.date_range('%i-12-01'%start_year,'%i-02-28'%(start_year+1),freq='D')
        for i in range(start_year+1,end_year):
            begin = i
            end = i+1
            winters=winters.union(pd.date_range('%i-12-01'%begin,'%i-02-28'%end,freq='D'))
        selected = self.dataset.sel(time=winters)
        return selected

    @cachedproperty
    def dataset(self):

        client = _get_global_client()
        if client is None:
            print(f'WARNING! No Dask client available in environment!')

        if self.var == 'eff_lat':

            self.dataset = xr.open_mfdataset(self.path_to_files,
                                        combine='by_coords',
                                        chunks=self.chunks,
                                        preprocess=self.preprocess_file)
        else:
            self.dataset = xr.open_mfdataset(self.path_to_files,
                                         chunks=self.chunks,
                                         combine='by_coords')
        if self.season == 'DJF':
           if 'era5' in self.path_to_files:
               _dataset = self.sel_winters(1980,2018)
           else:
               try:
                   self.dataset['time'] = self.dataset.indexes['time'].normalize()
               except AttributeError:
                   self.dataset['time'] = self.dataset.indexes['time'].to_datetimeindex().normalize()
               _dataset=self.sel_winters()
           return _dataset
        elif season == 'all':
           pass # self.dataset = self.dataset
        else:
            raise NotImplementedError

    @staticmethod
    def preprocess_file(array):
        var = list(array.variables.keys())[-1]
        array_new = array.rename({var: 'eff_lat'})
        array_new = array_new.sortby('time')
        return array_new

    @staticmethod
    def demean(data, decade=False):
        """ Calculate demeaned anomaly with daily and decadal baselines

        This function calculates the demeaded temperature by either calculating
        a day-of-the-year baseline mean, by default, or by calculating a decade mean.
        This operation is grid-based, so it is calculating daily and decade
        means. 

        Parameters
        ---------
            - decade bool: Demean by decades. Default is `False`.

        Returns
        ------
            xr.Dataset
        """

        if decade:
            decade_day_idx = pd.MultiIndex.from_arrays([(data.time.dt.year//10)*10, data.time.dt.dayofyear])
            data.coords['decade_day'] = ('time', decade_day_idx)
            grp_by = 'decade_day'
        else:
            grp_by = 'time.dayofyear'

        xr_mean = (data.
                   groupby(grp_by).
                   mean()
                   )

        demeaned = data.groupby(grp_by) - xr_mean

        return demeaned

    def demeaned_shift(self, ds):
        """ Shifted demeaned effective latitude 

        This function takes the demeaned effective latitude data and adds back
        the real latitude to get an infomative measurement of effective
        latitude instead of an anomaly. 

        Returns
        -------
            xr.Dataset
        """

        demeaned_array = self.demean(ds)
        demeaned_shift = demeaned_array + ds.lat

        return demeaned_shift

    def stats_calc(self,data):
        mean = data.mean(dim='time')#.rename({'t_prime':'tp_mean'})
        std = data.std(dim='time')#.rename({'t_prime':'tp_std'})
        skewness = xr.full_like(mean,
                                skew(data[self.var],axis=0), #skew(self.dataset.t_prime,axis=0),
                                dtype=np.float64)#.rename({'tp_mean':'tp_skew'})

        return xr.concat([mean,std,skewness],dim='stat').assign_coords({'stat':['mean','std','skew']})

    def diagnostic_stats(self,demean=False):
        if 'era5' in self.path_to_files:
            future = (2008,2018)
            present = (1980,1990)
        else:
            future = (2090,2100)
            present = (2015,2025)
        self.data_present = self.sel_winters(present[0],present[1])
        self.data_future = self.sel_winters(future[0],future[1])

        if demean:
           try:
               data_present_dm = self.data_present_dm
               data_future_dm = self.data_future_dm
           except AttributeError:
               data_present_dm = self.demean(self.data_present)
               data_future_dm = self.demean(self.data_future)
           self.stats_present = self.stats_calc(data_present_dm)
           self.stats_future = self.stats_calc(data_future_dm)
           self.stats_diff =  self.stats_future - self.stats_present

        else:
           self.stats_present = self.stats_calc(self.data_present)
           self.stats_future = self.stats_calc(self.data_future)
           self.stats_diff = self.stats_future - self.stats_present

    def diagnostic_plot(self, demean=False):
         self.diagnostic_stats(demean=demean)
         xr_all = xr.concat([self.stats_present,self.stats_future,self.stats_diff],dim='period').assign_coords({'period':['present','future','diff']})
         print('plotting...')
         p = xr_all.sel(stat='mean')[self.var].plot(transform = ccrs.PlateCarree(),
                                    col='period',
                                    subplot_kws={'projection': ccrs.Orthographic(20, 90)})
         for ax in p.axes.flat:
             ax.coastlines()
             ax.gridlines()
         plt.savefig(self.path_to_save+'diagnostic_mean.png')
         p = xr_all.sel(stat='std')[self.var].plot(transform = ccrs.PlateCarree(),
                                    col='period',
                                    subplot_kws={'projection': ccrs.Orthographic(20, 90)})
         for ax in p.axes.flat:
             ax.coastlines()
             ax.gridlines()
         plt.savefig(self.path_to_save+'diagnostic_std.png')
         p = xr_all.sel(stat='skew')[self.var].plot(transform = ccrs.PlateCarree(),
                                    col='period',
                                    subplot_kws={'projection': ccrs.Orthographic(20, 90)})
         for ax in p.axes.flat:
             ax.coastlines()
             ax.gridlines()
         plt.savefig(os.path.join(self.path_to_save, 'diagnostic_skew.png'))
