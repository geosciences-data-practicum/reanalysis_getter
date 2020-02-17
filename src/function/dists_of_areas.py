"""
Counting area at each temp bin 
Imputs: temperature array, latitude array, seq of temperature bin cut points
"""

import numpy as np

def dists_of_areas(temp_df,lat,Tbins):
    #weight entry by box area so that y axis is no longer the number of boxes, but rather the area taken up by each box
    #this is the area of each grid cell
    R_earth = 6367.47 #km
    dphi = 0.25*np.pi/180. #temperature data grid size, in radians
    areas = (R_earth*dphi)**2 * np.cos(lat)
    pdf_areas, binedges = np.histogram(temp_df,bins=Tbins,weights=areas)
    cdf_areas=np.cumsum(pdf_areas)
    return binedges[:-1], pdf_areas, cdf_areas
