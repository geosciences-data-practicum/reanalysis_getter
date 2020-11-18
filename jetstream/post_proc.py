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
import cartopy.crs as ccrs

class PostProcessor(object):
    
    def __init__(self,
                 path_to_files,
                 path_to_save_files=None,
		 diagnostic_var='t_prime',
                 season='DJF'):
        self.path_to_files = path_to_files
        self.path_to_save = path_to_save_files
        self.season = season
	self.var = diagnositc_var
	self.dataset = xr.open_mfdataset(self.path_to_files, combine='by_coords')
	if season == 'DJF':
	   self.dataset=self.sel_winters()
	elif season == 'all':
	   self.dataset = self.dataset()
	else:
	    raise NotImplementedError

    def sel_winters(self,start_year=2015,end_year=2099):
        winters = pd.date_range('%i-12-01'%start_year,'%i-02-28'%(start_year+1),freq='D')
        for i in range(start_year,end_year):
            begin = i+1
            end = i+2
            winters=winters.union(pd.date_range('%i-12-01'%begin,'%i-02-28'%end,freq='D'))
         
	selected = self.dataset.sel(time=winters)
	return selected

    def demean(self):
        xr_mean = self.dataset.\
                groupby('time.dayofyear').\
                mean().\
                compute()
        demeaned = self.dataset.groupby('time.dayofyear') - xr_mean
        return demeaned.compute()

    def stats_calc(self):
        mean = self.dataset.mean(dim='time')#.rename({'t_prime':'tp_mean'})
        std = self.dataset.std(dim='time')#.rename({'t_prime':'tp_std'})
        skewness = xr.full_like(mean,
                                skew(self.dataset[self.var],axis=0), #skew(self.dataset.t_prime,axis=0),
                                dtype=np.float64)#.rename({'tp_mean':'tp_skew'})

        return xr.concat([mean,std,skewness],dim='stat').assign_coords({'stat':['mean','std','skew']})

   def diagnostic_stats(self,demean=False):
	self.data_present = self.sel_winters(2015,2025)
	self.data_future = self.sel_winters(2089,2099)
	
	if demean:
	   data_present_dm = self.demean(data_present)
	   data_future_dm = self.demean(data_future)
	   self.stats_present = stats_calc(data_present_dm)
	   self.stats_future = stats_calc(data_future_dm)
	   self.stats_diff =  stats_future_dm - stats_present_dm

	else:
	   self.stats_present = stats_calc(data_present)
	   self.stats_future = stats_calc(data_future)
	   self.stats_diff = stats_future - stats_present
	

   def diagnostic_plot(self, var, demean=False):
	self.diagnostic_stats(demean=demean)
        xr_all = xr.concat([self.stats_present,self.stat_future,self.stats_diff],dim='period').assign_coords({'period':['present','future','diff']})
        p = xr_all.sel(stat='mean')[self.var].plot(transform = ccrs.PlateCarree(),
                                   col='period',
                                   subplot_kws={'projection': ccrs.Orthographic(20, 90)})
        for ax in p.axes.flat:
            ax.coastlines()
            ax.gridlines()
        p = xr_all.sel(stat='std')[self.var].plot(transform = ccrs.PlateCarree(),
                                   col='period',
                                   subplot_kws={'projection': ccrs.Orthographic(20, 90)})
	plt.savefig(self.path_to_save_files+
        for ax in p.axes.flat:
            ax.coastlines()
            ax.gridlines()
        p = xr_all.sel(stat='skew')[self.var].plot(transform = ccrs.PlateCarree(),
                                   col='period',
                                   subplot_kws={'projection': ccrs.Orthographic(20, 90)})
        for ax in p.axes.flat:
            ax.coastlines()
            ax.gridlines()