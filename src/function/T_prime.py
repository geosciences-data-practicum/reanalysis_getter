"""
Calculating T_prime 
Imputs: temperature array, latitude array, seq of temperature bin cut points
"""

import numpy as np
from dists_of_lat_eff import dists_of_lat_eff

def T_prime(temp_df,lat,Tbins):
    #take effective latitude cdf
    binedges,cdf_lat_eff = dists_of_lat_eff(temp_df,lat,Tbins)
    #calculate T_ref with just the latitude, given the effective lat vs temp contour relation
    #linear interpolation
    T_ref = np.interp(lat,np.flip(cdf_lat_eff),np.flip(binedges))
    #calculate T'(lat,lon) which is T_true(lat,lon,time) - T_ref(lat,lon,time)
    Tprime = T_ref - temp_df #this is a function of longitude and time
    return Tprime
