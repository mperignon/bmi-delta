import numpy as np
import os
from matplotlib import pyplot as plt



def random_pick(probs, num_options=8):
    '''
    Randomly pick a number weighted by array probs (len 8)
    Return the index of the selected weight in array probs
    '''

    if np.max(probs) == 0:
        probs = list([1/num_options for i in range(num_options)])

    cutoffs = np.cumsum(probs)
    idx = cutoffs.searchsorted(np.random.uniform(0, cutoffs[-1]))

    return idx



def random_pick_list(choices, probs = None):
    '''
    Randomly pick a number from array choices weighted by array probs
    Values in choices are column indices

    Return a tuple of the randomly picked index for row 0
    '''

    if not probs:
        probs = list([1 for i in range(len(choices))])

    cutoffs = np.cumsum(probs)
    idx = cutoffs.searchsorted(np.random.uniform(0, cutoffs[-1]))

    return (0,choices[idx])


    
def save_figure(path, ext='png', close=True):
    '''
    Save a figure from pyplot.

    path : string
        The path (and filename without extension) to save the figure to.
    ext : string (default='png')
        The file extension. This must be supported by the active
        matplotlib backend (see matplotlib.backends module).  Most
        backends support 'png', 'pdf', 'ps', 'eps', and 'svg'.
    '''

    directory = os.path.split(path)[0]
    filename = "%s.%s" % (os.path.split(path)[1], ext)
    if directory == '': directory = '.'

    if not os.path.exists(directory):
        os.makedirs(directory)

    savepath = os.path.join(directory, filename)
    plt.savefig(savepath)

    if close: plt.close()