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
from time import sleep

# Function source
def func_1(t, w, x):
    """
    A simple function (decaying exponential)
    """
    return np.exp((1j*w - x) * t)


def function_generator(t):
    """
    Creates a test function
    """
    """
    f1 = func_1(t, 50*2*np.pi, 5)
    #f2 = func_1(t, 243*2*np.pi, 3)
    result = f1# + f2
    echo1 = 0.5*(f1[:f1.size/2])# + f2[:f2.size/2])
    result[result.size/2:] += echo1
    echo2 = 0.3*(f1[:f1.size/4])# + f2[:f2.size/4])
    result[result.size*3/4:] += echo2
    """
    result = np.sin(500*2*np.pi*t)
    result[:int(len(t)/4)] *= 0
    result[int(len(t)*3/4):] *= 0
    return result


def fft_of_window(signal, window_lower, window_upper, window_shape):
    """
    Takes the Fourier Transform of a window of values in a signal
    """
    window_width = window_upper - window_lower
    # Scale window by window shape
    window_values = np.multiply(signal[window_lower:window_upper], window_shape)
    # Take FFT of scaled window
    return fft.rfft(window_values, n=window_width)


def sliding_window_fft(signal, signal_dt, fft_sample_freq, window_width, window_increment, window_shape=-1):
    """
    Takes successive Fourier Transforms of a window as it is slid across a 1D signal
    """
    ## Extend signal so that first time bin for FFT can be taken at t=0
    # This extends the signal so it has width/2 zeros before the signal and the same after the signal
    signal_extended = np.concatenate((np.zeros(window_width/2), signal, np.zeros(window_width/2)))

    ## Set up window
    # Default: Hanning
    if window_shape == -1:
        window_shape = np.hanning(window_width)
    window_lower = 0
    window_upper = window_lower + window_width

    ## Set up FFT
    i = 0
    FFT = np.zeros((np.floor(signal.size / window_width), window_width/2 + 1))

    ## Slide the window along and take FFTs
    for i in np.arange(FFT.shape[0]):
        # Take FFT of window
        FFT[i] = fft_of_window(signal_extended, window_lower, window_upper, window_shape)
        # Increment window
        window_lower += window_increment
        window_upper += window_increment

    ## Find associated frequencies of the FFT
    freqs = fft.fftfreq(window_width, signal_dt * 1/fft_sample_freq)

    return FFT, freqs


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
dt_t = 2e-5
# Create time vector
t = np.arange(0.0, len_t, dt_t)
# Create data
y = function_generator(t)


##################
# SONOGRAM       #
##################
# Set up variables for window of fft
width_W = 256
step_W = 32
N_W = int(y.size/step_W)

# Create data structure to store spectrogram in
t_spectrogram = np.linspace(t[int(width_W/2)], t[int(-(width_W/2))], N_W)
f = fft.fftfreq(width_W, dt_s) * dt_s / dt_t
sp = np.zeros((t_spectrogram.size, int(width_W/2) + 1))


# Set window properties
lower_W = 0
upper_W = lower_W + width_W
i = 0

window_221 = 0
sp_221 = 0

# Take FFT of sliding window
# Repeat until number of spectra reached
#while i < N_W:

while upper_W < y.size:
    print("Taking fft of window {}".format(i))
    sp[i] = fft_of_window(y, lower_W, upper_W, np.hanning(width_W))
    if i == 221:
        window_221 = np.multiply(y[lower_W:upper_W], np.hanning(width_W))
        sp_221 = sp[i]
    # Next spectrum
    i += 1
    # Increment lower bound of window
    lower_W += step_W
    # Increment uppper bound of window
    upper_W += step_W

# Take only positive frequencies
f = f[:int(len(f)/2) + 1]

# Create grid of data points
F, T = np.meshgrid(f, t_spectrogram)

# Find magnitude of freqency components
sp = np.abs(sp)

"""
Test
"""
"""
fig = plt.figure()
plt.ion()
plt.show()
ax = fig.add_subplot(111)
ax.set_xlim(0,500)
ax.set_ylim(0,100)
line1, = ax.plot(f, sp[0]) # Returns a tuple of line objects, thus the comma
i=0
while i < N_W:
    print("Window: " + str(i))
    line1.set_ydata(sp[i])
    plt.draw()
    plt.pause(0.01)
    i+=1
""" 

## Trying to find the frequency of modulation
# Amplitude-time plot at freq=500Hz:
plt.figure()
freq_500 = sp[:, 13]
plt.plot(t_spectrogram, freq_500)
plt.xlabel('Time (s)')
plt.ylabel('Amplitude') 

# Take FFT of slice at 500Hz
plt.figure()
FFT_500 = fft.rfft(freq_500)
FFT_freqs_500 = fft.fftfreq(len(freq_500), 1/4096)
plt.plot(FFT_freqs_500[:int(len(FFT_freqs_500)/2) + 1], FFT_500)
plt.xlabel('Freq of modulation (Hz)')
plt.ylabel('Amplitude')
plt.xlim(0)
plt.ylim(0)

#"""
# Plot sonogram
"""
# Contours:
fig_sonogram_cont = plt.figure()
contours = plt.contour(F, T, sp)
plt.xlabel('Freq (Hz)')
#plt.xlim(800, 1200)
plt.xlim(300,700)
plt.ylim(1,1.25)
plt.ylabel('Time (s)')
"""
"""
# Surface:
fig_sonogram_surf = plt.figure()
ax_s = fig_sonogram_surf.gca(projection='3d')
surf = ax_s.plot_surface(F, T, sp, linewidth=0, cmap=cm.jet)
ax_s.set_xlabel('Freq (Hz)')
ax_s.set_xlim(500, 1500)
ax_s.set_ylabel('Time (s)')
ax_s.set_zlabel('Amplitude')

# Colourmap:
fig_sonogram_color = plt.figure()
plt.pcolormesh(F, T, sp)
plt.xlabel('Freq (Hz)')
plt.xlim(500, 1500)
plt.ylabel('Time (s)')
"""
#"""
# Window 221
# This is an example of a window that didn't work in the FFT window-sliding loop (sp = 0) - yet when recalculated worked fine
fig_221_sig = plt.figure()
plt.suptitle("Window 221: Signal")
plt.plot(np.arange(0,256), window_221)
plt.legend(['Signal'])

fig_221_freq = plt.figure()
plt.suptitle("Window 221: Frequency")
plt.plot(f, np.abs(sp_221))

sp_221_calc = fft.rfft(window_221, n=width_W)
plt.plot(f, np.abs(sp_221_calc))
plt.xlim(0)
plt.legend(['Spectrum', 'Recalculated Spectrum'])
#"""

# Display graphs
plt.show()

