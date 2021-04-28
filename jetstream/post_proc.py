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
                 path_to_input_files,
                 chunks={'time': 1},
                 diagnostic_var='t_prime',
                 season='DJF'):
        self.chunks = chunks
        self.path_to_files = path_to_input_files
        self.season = season
        self.var = diagnostic_var

    def sel_winters(self,data,start_year=2015,end_year=2100):
        winters = pd.date_range('%i-12-01'%start_year,'%i-02-28'%(start_year+1),freq='D')
        for i in range(start_year+1,end_year):
            begin = i
            end = i+1
            winters=winters.union(pd.date_range('%i-12-01'%begin,'%i-02-28'%end,freq='D'))
        selected = data.sel(time=winters)
        return selected

    @cachedproperty
    def dataset(self):

        client = _get_global_client()
        if client is None:
            print(f'WARNING! No Dask client available in environment!')

        _full_dataset = xr.open_mfdataset(self.path_to_files,
                                         chunks=self.chunks,
                                         concat_dim='time',
                                         preprocess=self.preprocess_mf)
        self.year_range = np.unique(_full_dataset.time.dt.year)[[0,-1]]
        if self.season == 'DJF':
            try:
               _full_dataset['time'] = _full_dataset.indexes['time'].normalize()
            except AttributeError:
               _full_dataset['time'] = _full_dataset.indexes['time'].to_datetimeindex().normalize()
            _dataset=self.sel_winters(_full_dataset,*self.year_range)
            return _dataset
        elif season == 'all':
           return _full_dataset
        else:
            raise NotImplementedError

    @staticmethod
    def preprocess_mf(array):
        var = list(array.variables.keys())[-1]
        if var not in ['eff_lat','t_prime']:
            array = array.rename({var: 'eff_lat'})
            var='eff_lat'
        array_filter = array.where(array[var] != 0)
        array_new = array.sortby('time')
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
            #data = data.assign_coords(year=('time',
            #    group_into_winters(data.time)))
            decade_day_idx = pd.MultiIndex.from_arrays(
                    [((data.time.dt.year//10)*10).data,
                        data.time.dt.dayofyear.data])
            data.coords['decade_day'] = ('time', decade_day_idx)
            grp_by = 'decade_day'
        else:
            grp_by = 'time.dayofyear'

        xr_mean = (data.
                   groupby(grp_by).
                   mean()
                   )

        demeaned = data.groupby(grp_by) - xr_mean
        return demeaned.drop('decade_day',errors='ignore')

    def demeaned_shift(self, data, decade=False):
        """ Shifted demeaned effective latitude

        This function takes the effective latitude data, demeans it, and adds back
        the real latitude to get an infomative measurement of effective
        latitude instead of an anomaly.

        Returns
        -------
            xr.Dataset
        """

        demeaned_array = self.demean(data, decade=decade)
        demeaned_shift = demeaned_array + data.lat

        return demeaned_shift

    def stats_calc(self,data):
        try:
            data = data.drop('expver')
        except ValueError:
            pass
        mean = data.mean(dim='time')[self.var]
        std = data.std(dim='time')[self.var]
        skewness = xr.DataArray(
                data=skew(data[self.var], nan_policy='omit'),
                dims=mean.dims,
                coords=mean.coords
                )
        #statistics = xr.Dataset(dict(stats=(
        #    ['stat','lat','lon'],[
        #    mean,
        #    std,
        #    xr.ones_like(mean)*skewness
        #    ])
        #    ),
        #    coords={'stat':['mean','std','skewness'],
        #        'lat':mean.lat,'lon':mean.lon}
        #    )
        statistics=xr.concat(
            [mean,std,skewness],#skewness*xr.ones_like(mean)],
            dim='stat'
            ).assign_coords({'stat':['mean','std','skew']})
        return statistics

    def diagnostic_stats(self,demean=False):
        data=self.dataset
        present = (self.year_range[0],self.year_range[0]+10)
        future = (self.year_range[-1]-10,self.year_range[-1])
        self.data_present = self.sel_winters(data,*present)
        self.data_future = self.sel_winters(data,*future)

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

    def diagnostic_plot(self, demean=False, path_to_save="./"):
         self.diagnostic_stats(demean=demean)
         xr_all = xr.concat([
             self.stats_present,
             self.stats_future,
             self.stats_diff],
             dim='period').assign_coords({
                 'period':['first_decade','last_decade','difference']
                 })
         xr_all.to_netcdf(path_to_save+'_statistics.nc4')
         print('plotting...')
         p = xr_all.sel(stat='mean').plot.imshow(
                 transform=ccrs.PlateCarree(),
                 col='period',
                 subplot_kws={
                     'projection':ccrs.Orthographic(20, 90)
                     }
                 )
         for ax in p.axes.flat:
             ax.coastlines()
             ax.gridlines()
         plt.savefig(path_to_save+'_mean.png')
         p = xr_all.sel(stat='std').plot.imshow(
                 transform = ccrs.PlateCarree(),
                 col='period',
                 subplot_kws={
                     'projection': ccrs.Orthographic(20, 90)
                     }
                 )
         for ax in p.axes.flat:
             ax.coastlines()
             ax.gridlines()
         plt.savefig(path_to_save+'_std.png')
         p = xr_all.sel(stat='skew').plot.imshow(
                 transform=ccrs.PlateCarree(),
                 col='period',
                 subplot_kws={
                     'projection':ccrs.Orthographic(20, 90)
                     }
                 )
         for ax in p.axes.flat:
             ax.coastlines()
             ax.gridlines()
         plt.savefig(path_to_save+'_skew.png')


#---- helper functions ----#
def run_demeaning(path_processed,
        shortname,
        path_postproc,
        var_of_interest,
        decade=False):
    #create class
    single = SingleModelPostProcessor(path_to_input_files=path_processed,
         diagnostic_var=var_of_interest,
         season='DJF')
    #demean or shift
    if var_of_interest =='t_prime':
        filename=path_postproc+f'{shortname}_{var_of_interest}_demeaned.nc4'
        single.demean(single.dataset.t_prime,
                decade=decade).rename('dm_t_prime'
                                            ).to_netcdf(filename)
    elif var_of_interest == 'eff_lat':
        filename=path_postproc+f'{shortname}_{var_of_interest}_demeaned_shifted.nc4'
        single.demeaned_shift(single.dataset,
                decade=decade).rename({var_of_interest: 'phi_eq_prime'}
                        ).to_netcdf(filename)
    return single

def group_into_winters(dates):
    year_arr = np.zeros(len(dates),dtype=int)
    y=0
    for date in dates:
        if date.dt.month <= 3:
            year_arr[y] = date.dt.year - 1
        else:
            year_arr[y] = date.dt.year
        y+=1
    return year_arr
