"""
Sonogram
Author: Theo Brown (tab53)
Date: July 2017
"""

from numpy import fft
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from scipy import signal


# Function source
def func_1(t, w, x):
    """
    A simple function (decaying exponential)
    """
    return np.exp((1j*w - x) * t)


def function_generator(t):
    """
    Creates a test function with echoes
    """
    f1 = func_1(t, 50*2*np.pi, 5)
    f2 = func_1(t, 243*2*np.pi, 3)
    result = f1 + f2
    echo1 = 0.5*(f1[:f1.size/2] + f2[:f2.size/2])
    result[result.size/2:] += echo1
    echo2 = 0.3*(f1[:f1.size/4] + f2[:f2.size/4])
    result[result.size*3/4:] += echo2
    return result


# Sampling information:
# Sampling frequency
f_s = 4096
# Sampling interval
dt_s = 1/f_s

## Create time series
# Length of time series
len_t = 2
# Number of points
# N_t = 4e3
# Interval between points
dt_t = 1e-4
# Create time vector
t = np.arange(0.0, len_t, dt_t)
# Create data
y = function_generator(t)

# Plot data
fig_y = plt.figure()
plt.plot(t, y)

"""
## Fourier Transform
# Take FFT of data
sp = fft.fft(y)
# Find associated frequencies
f = fft.fftfreq(y.size, dt_s) * dt_s * 1e3
# Take only positive part of FFT (?)
sp = sp[:sp.size/2]
f = f[:f.size/2]

# Plot FFT
fig_sp = plt.figure()
plt.plot(f, np.abs(sp))
plt.xlabel('Freq (Hz)')
plt.ylabel('Amplitude')
"""

##################
# SONOGRAM       #
##################
# Set up variables for window of fft
width_W = 256
step_W = 4
N_W = int(y.size/step_W)

# Create data structure to store spectrogram in
t = np.linspace(0, len_t, N_W)
sp = np.zeros((t.size, width_W))
f = fft.fftfreq(width_W, dt_s) * dt_s / dt_t

# Set window properties
lower_W = 0
upper_W = lower_W + width_W

i = 0

# Take FFT of sliding window
# Repeat until number of spectra reached
while i < N_W:
    print("Taking fft of window {}".format(i))
    # Take FFT of window
    sp[i] = fft.fft(y[lower_W:upper_W], n=sp[i].size)
    # Next spectrum
    i += 1
    # Increment lower bound of window
    lower_W += step_W
    # Increment uppper bound of window
    upper_W += step_W


# Take only positive part of FFT (?)
sp = sp[:, :sp.shape[1]/2]
f = f[:len(f)/2]

# Create grid of data points
F, T = np.meshgrid(f, t)

# Find magnitude of freqency components
sp = np.abs(sp)

# Plot sonogram
# Contours:
fig_sonogram_cont = plt.figure()
contours = plt.contour(F, T, sp)
plt.xlabel('Freq (Hz)')
plt.xlim(0, 1000)
plt.ylabel('Time (s)')

# Surface:
fig_sonogram_surf = plt.figure()
ax = fig_sonogram_surf.gca(projection='3d')
surf = ax.plot_surface(F, T, sp, linewidth=0, cmap=cm.coolwarm)
ax.set_xlabel('Freq (Hz)')
ax.set_xlim(0, 1000)
ax.set_ylabel('Time (s)')
ax.set_zlabel('Amplitude')

# Colourmap:
fig_sonogram_color = plt.figure()
plt.pcolormesh(F, T, sp)
plt.xlabel('Freq (Hz)')
plt.xlim(0, 1000)
plt.ylabel('Time (s)')

# Display graphs
plt.show()
