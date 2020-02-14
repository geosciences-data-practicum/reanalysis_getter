"""
Convert np to xarray for plotting on globes
Imputs: normal array
"""

import numpy as np
import xarray as xr

def convert_to_xarray(sequence):
    """this assumes a very specific structure to the sequence 
    (0.25 deg resolution on regular grid, latitudes only above 20 deg)
    that probably only works for the specific data array I am using in this notebook"""
    #hard code my coords because I'm only going to use this
    latitude_coords = np.flip(np.arange(20.25,90.001,step=0.25))
    longitude_coords = np.arange(0,360,step=0.25)

    z = np.array(sequence).reshape((280,1440))
    xarr = xr.DataArray(z,
                       dims = ('lat','lon'),
                       coords={'lat':latitude_coords,'lon':longitude_coords})

    return xarr
