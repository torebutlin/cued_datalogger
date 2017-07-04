"""
Sonogram
Author: Theo Brown (tab53)
"""

from numpy import fft
import numpy as np
import matplotlib.pyplot as plt

# Sampling information:
# Number of samples
sample_N = 4096
# Sampling frequency
sample_freq = 4096
sample_w = sample_freq * 2*np.pi
# Time interval between samples
dw = sample_w/sample_N

# Time series information:
# Length of time series
time_length = 1
# Number of points
time_N = 1e3
# Time interval between points
dt = time_length / time_N


# Function generator
def source_function(t, w=200*2*np.pi, x=5):
    return np.real(np.exp((1j*w - x) * t))


# Create time range
t = np.arange(0.0, time_length, dt)
# Create data
y = source_function(t)

# Plot data
fig_y = plt.figure()
plt.plot(t, y)


# Take FFT of data
sp = fft.fft(y)
# Find associated frequencies
f = fft.fftfreq(t.size, 1/sample_freq)
# f = np.linspace(0, sample_w * (sample_N - 1)/sample_N, sample_N)

# Plot FFT
fig_sp = plt.figure()
plt.plot(f, 20*np.log10(np.abs(sp)))

##################
# SONOGRAM       #
##################
# Set up variables for window of fft
window_size = 256
window_step = 64
window_N = int(y.size/window_step)

# Create data structure to store spectrogram in
sp = np.zeros((t.size, t.size))
f = fft.fftfreq(t.size, 1/sample_freq)

i = 0
lower = 0
upper = lower + window_size

# Take FFT of sliding window
# Repeat until number of spectra reached
while i < window_N:
    print("Taking fft of window {}".format(i))
    # Take FFT of window
    sp[i] = fft.fft(y[lower:upper], n=t.size)
    # Next spectrum
    i += 1
    # Increment lower bound of window
    lower += window_step
    # Increment uppper bound of window
    upper += window_step


# Create grid of data points
F, T = np.meshgrid(f, t)

# Plot sonogram
fig_sonogram_cont = plt.figure()
contours = plt.contour(F, T, sp)

# Display graphs
plt.show()
