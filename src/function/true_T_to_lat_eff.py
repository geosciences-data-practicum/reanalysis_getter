"""
Calculating effective latitude based on real temperatures 
Imputs: temperature array, latitude array, cdf of effective latitude function including binedges and cdf arrays
"""

import numpy as np

def true_T_to_lat_eff(temp_df,lat,binedges,cdf_lat_effs):
    #calculate effective latitude
    lat_eff = np.interp(temp_df,binedges,cdf_lat_effs)
    #calculate difference to real latitude
    phi_prime = lat - lat_eff
    return lat_eff, phi_prime
