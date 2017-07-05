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
def func_1(t, w, x):
    return np.exp((1j*w - x) * t)

def func_2(t, w):
    return np.sin(w*t)

def function_generator(t):
    """
    f1 = func_1(t, 50*2*np.pi, 5)
    f2 = func_1(t, 80*2*np.pi, 3)
    f1_echo = f1/3
    f2_echo = f2/4
    result = f1 + f2
    echo = f1_echo[:f1_echo.size/2] + f2_echo[:f2_echo.size/2]
    result[result.size/2:] += echo
    """
    f1 = func_2(t, 50*2*np.pi)
    f2 = func_2(t, 80*2*np.pi)
    result = f1 + 0.5*f2
    result[result.size/4:result.size/2] *= 0
    result[result.size*3/4:] *= 0
    return result

def dB(x):
    return 20*np.log10(x)

# Sampling information:
# Sampling frequency
f_s = 44.1e3
# Sampling interval
dt_s = 1/f_s

## Create time series
# Length of time series
len_t = 2
# Number of points
#N_t = 4e3
# Interval between points
dt_t = 1e-3
# Create time vector
t = np.arange(0.0, len_t, dt_t)
# Create data
y = function_generator(t)

# Plot data
fig_y = plt.figure()
plt.plot(t, y)

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


##################
# SONOGRAM       #
##################
# Set up variables for window of fft
width_W = 256
step_W = 32
N_W = int(y.size/step_W)

# Create data structure to store spectrogram in
sp = np.zeros((t.size, width_W))
f = fft.fftfreq(width_W, dt_s) * dt_s * 1e3

i = 0
lower_W = 0
upper_W = lower_W + width_W

# Take FFT of sliding window
# Repeat until number of spectra reached
while i < N_W:
    print("Taking fft of window {}".format(i))
    # Take FFT of window
    sp[lower_W] = fft.fft(y[lower_W:upper_W], n=sp[lower_W].size)
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

sp = np.abs(sp)

# Plot sonogram
fig_sonogram_cont = plt.figure()
contours = plt.contour(F, T, sp)

fig_sonogram_surf = plt.figure()
ax = fig_sonogram_surf.gca(projection='3d')
surf = ax.plot_surface(F, T, sp, linewidth=0, cmap=cm.coolwarm)
"""
fig_sonogram_color = plt.figure()
plt.pcolormesh(t, f, sp)
"""

# Built in functions:
fig_spectrogram = plt.figure()
f, t, Sxx = signal.spectrogram(y, f_s)
plt.pcolormesh(t, f, Sxx)
plt.ylabel('Frequency [Hz]')
plt.xlabel('Time [sec]')

# Display graphs
plt.show()
