"""
Calculating effective latitude based on real temperatures 
Imputs: temperature array, latitude array, seq of temperature bin cut points
"""

import numpy as np
from dists_of_lat_eff import dists_of_lat_eff

def true_T_to_lat_eff(temp_df,lat,Tbins):
    #take effective latitude cdf
    binedges,cdf_lat_effs = dists_of_lat_eff(temp_df,lat,Tbins)
    #calculate effective latitude
    lat_eff = np.interp(temp_df,binedges,cdf_lat_effs)
    #calculate difference to real latitude
    phi_prime = lat - lat_eff
    return lat_eff, phi_prime
