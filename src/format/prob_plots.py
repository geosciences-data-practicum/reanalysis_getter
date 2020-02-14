"""
Plotting probability distributions
Imputs: x-axis temperature bin edges, cdf/pdf arrays, x-axis label as a string
"""

import matplotlib.pyplot as plt

def prob_plots(binedges,dist,xlab,cdf=None):
    if cdf is not None:
        plt.plot(binedges,cdf,label='cdf')
    plt.plot(binedges,pdf,label='pdf')
    plt.xlabel('bin edges [temp]')
    plt.ylabel(xlab)
    plt.legend()
    plt.show()
