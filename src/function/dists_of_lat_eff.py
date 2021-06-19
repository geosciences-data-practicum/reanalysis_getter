"""
Compute effective lattitude CDF 
Imputs: temperature array,latitude array, seq of temperature bin cut points
"""

import numpy as np
from dists_of_areas import dists_of_areas

def dists_of_lat_eff(temp_df,lat,Tbins):
    #first obtain cdf of areas
    R_earth = 6367.47 #km
    dphi = 0.25*np.pi/180. #radians, this is also dlambda
    binedges,pdf_areas,cdf_areas = dists_of_areas(temp_df,lat,Tbins)
    #A = 2piR^2 (1-sin(lat_eff))
    #so 1-A/(2piR^2) = sin(lat_eff)
    #but remember latitude is defined to start at pi at the north pole
    cdf_lat_eff = np.pi/2.-np.arccos(1-cdf_areas / (2*np.pi*R_earth**2) )
    return binedges, cdf_lat_eff