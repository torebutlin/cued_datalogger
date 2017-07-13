from scipy.signal import spectrogram, get_window
import numpy as np

from pyqtgraph.Qt import QtGui, QtCore 
import pyqtgraph as pg

import sys

from mypyqtgraph_functions import plot_contours

def func_1(t, w, x, k=0):
    """A simple decaying sine wave function."""
    return np.exp((1j*w - x)*t)


def function_generator(t):
    """A simple function generator with echoes."""
    f1 = func_1(t, 2000*2*np.pi, 2)
    f2 = func_1(t, 500*2*np.pi, 1)
    # Create an echo of one of the functions
    f1[f1.size//2:] += f1[:f1.size//2]
    result = f1 + f2
    return result

num_contours = 32
sample_freq = 4096
window_width = 256
window_increment = 32

duration = 10.0
t = np.arange(0.0, duration, 1/4096)
sig = function_generator(t)

freqs, times, FT = spectrogram(sig, sample_freq, 
                               window=get_window('hann', window_width),
                               noverlap=(window_width - window_increment))
FT = FT.transpose()
        
FT = np.abs(FT[:, :FT.shape[1] // 2 + 1])
        
freqs = np.abs(freqs[:freqs.size // 2 + 1])

F_bins, T_bins = np.meshgrid(freqs, times)

spacing = (FT.max() - FT.min()) / num_contours

contour_plot = plot_contours(freqs, times, FT, num_contours=num_contours, contour_spacing=spacing)
contour_plot.setLabel('bottom', "Frequency", "Hz")
contour_plot.setLabel('left', "Time", "s")

if __name__ == '__main__':
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
