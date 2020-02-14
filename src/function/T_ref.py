"""
Compute reference temperature CDF 
Imputs: temperature array,latitude array, seq of temperature bin cut points
"""

import numpy as np
from dists_of_lat_eff import dists_of_lat_eff

def T_ref(temp_df,lat,Tbins):
    #first obtain cdf of effective lat
    binedges,cdf_lat_effs = dists_of_lat_eff(temp_df,lat,Tbins)
    #interpolate to get T_ref
    T_ref = np.interp(lat,np.flip(cdf_lat_effs),np.flip(binedges))
    return binedges, T_ref
