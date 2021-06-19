"""
Calculating delta-T relative to zonal mean of the same latitude band for given places
Imputs: dataframe including T, latitude, longitude columns, given places lat lon as a dictionary
"""

import numpy as np
import pandas as pd

def deltaT(df,places):
    #bands of latitude
    lat_groups = df.groupby('latitude')
    #pixel group
    pixel_groups = df.groupby(['latitude','longitude'])
    #initialize
    deltaT_pd = pd.DataFrame(np.zeros((522,len(places))),columns=places.key())
    #loop through all places
    for place in places: 
        print(place)
        temp_there = pixel_groups.get_group(places[place]).t2m
        ref_temp = lat_groups.get_group(places[place][0]).t2m.mean()
        deltaT_pd[place] = ref_temp - temp_there
    deltaT_pd = deltaT_pd.drop('time',axis=1)
    return deltaT_pd
