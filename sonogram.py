"""
Sonogram
Author: Theo Brown (tab53)
"""

from numpy import fft
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from scipy import signal

# Function source
def function_generator(t, w=50*2*np.pi, x=5):
    return np.real(np.exp((1j*w - x) * t))
    #return np.sin(50.0 * 2.0*np.pi*t) + 0.5*np.sin(80.0 * 2.0*np.pi*t)

# Sampling information:
# Sampling frequency
f_s = 4096
# Sampling interval
dt_s = 1/f_s

## Create time series
# Number of points
N_t = 1e3
# Interval between points
dt_t = 1e-3
# Create time vector
t = np.arange(0.0, N_t*dt_t, dt_t)
# Create data
y = function_generator(t)

# Plot data
fig_y = plt.figure()
plt.plot(t, y)

## Fourier Transform
# Take FFT of data
sp = fft.fft(y)
# Find associated frequencies
f = fft.fftfreq(y.size, dt_s)

# Plot FFT
fig_sp = plt.figure()
#plt.plot(f, 20*np.log10(np.abs(sp)))
plt.plot(f, np.abs(sp))

##################
# SONOGRAM       #
##################
# Set up variables for window of fft
width_W = 256
step_W = 64
N_W = int(y.size/step_W)

# Create data structure to store spectrogram in
sp = np.zeros((t.size, t.size))
f = fft.fftfreq(t.size, 1/f_s)

i = 0
lower_W = 0
upper_W = lower_W + width_W

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


# Create grid of data points
F, T = np.meshgrid(f, t)

# Plot sonogram
fig_sonogram_cont = plt.figure()
contours = plt.contour(F, T, sp)

fig_sonogram_surf = plt.figure()
ax = fig_sonogram_surf.gca(projection='3d')
surf = ax.plot_surface(F, T, sp, linewidth=0, cmap=cm.coolwarm)

fig_sonogram_color = plt.figure()
plt.pcolormesh(t, f, sp)

"""
# Built in functions:
fig_spectrogram = plt.figure()
f, t, Sxx = signal.spectrogram(y, f_s)
plt.pcolormesh(t, f, Sxx)
plt.ylabel('Frequency [Hz]')
plt.xlabel('Time [sec]')
plt.show()
"""
# Display graphs
plt.show()
