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
    f1 = func_1(t, 1000*2*np.pi, 5)
    #f2 = func_1(t, 4000*2*np.pi, 3)
    result = f1# + f2
    echo1 = f1[:int(f1.size/2)] #+ f2[:int(f2.size/2)]
    result[int(result.size/2):] += echo1
    #echo2 = 0.3*(f1[:int(f1.size/4)] + f2[:int(f2.size/4)])
    #result[int(result.size*3/4):] += echo2
    """
    result = np.sin(500*2*np.pi*t)
    #result[:int(len(t)/4)] *= 0
    #result[int(len(t)*3/4):] *= 0
    """
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


def sliding_window_fft(t, signal, fft_sample_freq=4096, window_width=256, window_increment=32, window_shape='hanning'):
    """
    Takes successive Fourier Transforms of a window as it is slid across a 1D signal
    """
    ## Extend signal so that first time bin for FFT can be taken at t=0
    # This extends the signal so it has width/2 zeros before the signal and the same after the signal
    signal_extended = np.append(np.zeros(int(window_width/2)), signal)
    signal_extended = np.append(signal_extended, np.zeros(int(window_width/2)))

    ## Set up window
    # Default: Hanning
    if window_shape == 'hanning':
        window_shape = np.hanning(window_width)
    else:
        raise ValueError("Unrecognised window shape.")
    window_lower = 0
    window_upper = window_lower + window_width

    ## Set up FT
    FT = np.zeros((int(signal.size / window_width), int(window_width/2) + 1))

    ## Find associated frequencies of the FT
    freqs = fft.rfftfreq(window_width, 1./fft_sample_freq)

    ## Find associated time bins of the FT
    FT_t = np.linspace(0, t[-1], num=FT.shape[0])

    ## Slide the window along and take FFTs
    for i in np.arange(FT.shape[0]):
        # Take FFT of window
        FT[i] = fft_of_window(signal_extended, window_lower, window_upper, window_shape)
        # Increment window
        window_lower += window_increment
        window_upper += window_increment
        i+=1

    return freqs, FT_t, FT


# Define sampling frequency
sample_freq = 4096
## Create time series
# Length of time series
len_t = 10
# Interval between points
dt_t = 1/sample_freq
# Create time vector
t = np.arange(0.0, len_t, dt_t)
# Create data
y = function_generator(t)
#plt.figure()
#plt.plot(t, y)

##################
# SONOGRAM       #
##################
## Calculate sonogram
freqs, FT_t, FT = sliding_window_fft(t, y, fft_sample_freq=sample_freq, window_increment=64)

# Create grid of data points
FREQS, FT_T = np.meshgrid(freqs, FT_t)

# Find magnitude of freqency components
FT = np.abs(FT)

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
"""

# Plot sonogram
# Contours:
fig_sonogram_cont = plt.figure()
contours = plt.contour(FREQS, FT_T, FT)
plt.xlabel('Freq (Hz)')
#plt.xlim(800, 1200)
#plt.xlim(300,700)
#plt.ylim(1,1.25)
plt.ylabel('Time (s)')

"""
# Surface:
fig_sonogram_surf = plt.figure()
ax_s = fig_sonogram_surf.gca(projection='3d')
surf = ax_s.plot_surface(FREQS, FT_T, FT, linewidth=0, cmap=cm.jet)
ax_s.set_xlabel('Freq (Hz)')
#ax_s.set_xlim(500, 1500)
ax_s.set_ylabel('Time (s)')
ax_s.set_zlabel('Amplitude')
"""
"""
# Colourmap:
fig_sonogram_color = plt.figure()
plt.pcolormesh(FREQS, FT_T, FT)
plt.xlabel('Freq (Hz)')
plt.xlim(500, 1500)
plt.ylabel('Time (s)')

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
fact = np.abs(sp_221_calc)/np.abs(sp_221)
"""

# Display graphs
plt.show()

