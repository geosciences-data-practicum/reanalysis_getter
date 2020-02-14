"""
Counting number of boxes at each temp bin 
Imputs: temperature array, seq of temperature bin cut points
"""

import numpy as np

def dists_of_boxes(temp_df,Tbins):
    #number of boxes at each temp
    pdf_boxes, binedges = np.histogram(temp_df,bins=Tbins)
    #number of boxes below each temp
    cdf_boxes=np.cumsum(pdf_boxes)
    return binedges[:-1], pdf_boxes, cdf_boxes
