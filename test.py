"""
Sonogram
Author: Theo Brown (tab53)
Date: July 2017
"""

from numpy import fft
import numpy as np
import matplotlib.pyplot as plt


def plot_test(x, y):
    plt.figure()
    plt.plot(x, y)
    plt.show()

def function_generator(t):
    """
    Creates a test function
    """
    result = np.sin(1000*2*np.pi*t)
    result[:t.shape[0]/4] *= 0
    result[t.shape[0]*3/4:] *= 0
    return result


def fft_of_window(signal, window_lower, window_upper, window_shape):
    """
    Takes the Fourier Transform of a window of values in a signal
    """
    window_width = window_upper - window_lower
    # plot_test(np.linspace(0, window_width, window_width), signal[window_lower:window_upper])
    # Scale window by window shape
    window_values = np.multiply(signal[window_lower:window_upper], window_shape)
    # plot_test(np.linspace(0, len(window_values), len(window_values)), window_values)
    # Take FFT of scaled window
    return fft.rfft(window_values, n=window_width)


def sliding_window_fft(t, signal, fft_sample_freq=4096, window_width=256, window_increment=32, window_shape=-1):
    """
    Takes successive Fourier Transforms of a window as it is slid across a 1D signal
    """
    ## Extend signal so that first time bin for FFT can be taken at t=0
    # This extends the signal so it has width/2 zeros before the signal and the same after the signal
    signal_extended = np.concatenate((np.zeros(window_width/2), signal, np.zeros(window_width/2)))
    """
    plt.figure("Signal_extended")
    plt.plot(np.linspace(0, len(signal_extended), len(signal_extended)), signal_extended)
    plt.show()
    """

    ## Set up window
    # Default: Hanning
    #if window_shape == -1:
    window_shape = np.hanning(window_width)
    window_lower = 0
    window_upper = window_lower + window_width

    ## Set up FT
    FT = np.zeros((signal.size / window_width, window_width/2 + 1))

    ## Find associated frequencies of the FT
    freqs = fft.fftfreq(window_width, (t[1] - t[0]) / fft_sample_freq)
    # Take only positive freqs
    freqs = freqs[:len(freqs)/2 + 1]

    ## Find associated time bins of the FT

    FT_t = np.linspace(0, t[-1], num=FT.shape[0])

    ## Slide the window along and take FFTs
    for i in np.arange(FT.shape[0]):
        # Take FFT of window
        print("FFTing " + str(i))
        print("t=" + str(FT_t[i]))
        #plot_test(np.linspace(0, len(signal_extended), len(signal_extended)), signal_extended)
        if(FT_t[i] > 0.5):
            print(window_lower)
            print(window_upper)
            print(signal[window_lower:window_upper])
            plot_test(np.linspace(0, len(signal_extended), len(signal_extended)), signal_extended)
            # plot_test(np.linspace(0, window_width, window_width), signal[window_lower:window_upper])
        FT[i] = fft_of_window(signal_extended, window_lower, window_upper, window_shape)
        #print(FT[i])
        # Increment window
        window_lower += window_increment
        window_upper += window_increment
        i+=1

    return freqs, FT_t, FT


## Create time series
# Create time vector
duration = 2
dt = 1e-4
t = np.arange(0.0, duration, dt)
# Create data
y = function_generator(t)
"""
plt.figure()
plt.plot(t,y)
plt.show()
"""

freqs, FT_t, FT = sliding_window_fft(t, y)

# Create grid of data points
FREQS, FT_T = np.meshgrid(freqs, FT_t)

# Find magnitude of freqency components
FT = np.abs(FT)

# Plot sonogram
# Contours:
fig_sonogram_cont = plt.figure()
contours = plt.contour(FREQS, FT_T, FT)
plt.xlabel('Freq (Hz)')
plt.xlim(0, 1000)
plt.ylabel('Time (s)')


# Display graphs
plt.show()
