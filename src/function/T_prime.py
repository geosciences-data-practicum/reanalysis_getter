"""
Calculating T_prime 
Imputs: temperature array, latitude array, seq of temperature bin cut points
"""

import numpy as np
from T_ref import T_ref

def T_prime(temp_df,lat,Tbins):
    #take effective latitude cdf
    binedges,Tref = T_ref(temp_df,lat,Tbins)
    #calculate T'(lat,lon) which is T_true(lat,lon,time) - T_ref(lat,lon,time)
    Tprime = temp_df - Tref #this is a function of longitude and time
    return Tprime
