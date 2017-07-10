"""
Sonogram
Author: Theo Brown (tab53)
Date: July 2017
"""

from numpy.fft import rfft, rfftfreq
import numpy as np
import matplotlib.pyplot as plt

SAMPLE_FREQ = 4096
WINDOW_WIDTH = 256
WINDOW_INCREMENT = 32


def func_1(t, w, x, k=0):
    """
    A simple decaying sine wave function
    """
    return np.exp((1j*w - x)*t)


def function_generator(t):
    """
    A function with echoes
    """
    f1 = func_1(t, 2000*2*np.pi, 2)
    f2 = func_1(t, 500*2*np.pi, 1)
    # Create an echo of one of the functions
    f1[np.floor(f1.size/2):] += f1[:np.floor(f1.size/2)]
    result = f1 + f2
    return result


def window_fft(signal, window_lower, window_upper, window_shape):
    """
    Takes the FT of a window within a signal, scaled by a shape array
    """
    window = np.multiply(signal[window_lower:window_upper], window_shape)

    return np.abs(rfft(window))


def sliding_window_fft(signal, t, window_shape):
    """
    Takes the FT of a shaped window as it is incremented across a signal
    """
    num_windows = np.floor(signal.size / WINDOW_INCREMENT)

    # Create the array to store the FT results in
    FT = np.zeros((num_windows, WINDOW_WIDTH/2 + 1))

    # Find the associated time vector and frequencies for the FT
    times = np.linspace(0, t[-1], num=num_windows)
    freqs = rfftfreq(WINDOW_WIDTH, 1/SAMPLE_FREQ)

    # Extend the signal so that the window can be slid off the ends
    signal_extended = np.append(np.zeros(int(WINDOW_WIDTH/2)), signal)
    signal_extended = np.append(signal_extended, np.zeros(int(WINDOW_WIDTH/2)))

    # Iterate through the signal taking FTs of each window
    for i in np.arange(num_windows):
        lower = i * WINDOW_INCREMENT
        upper = lower + WINDOW_WIDTH

        FT[i] = window_fft(signal_extended, lower, upper, window_shape)

    return freqs, times, FT


def sonogram(signal, t):
    """
    Plots a sonogram (frequencies present over time) of a signal
    """
    # Create the window
    hanning = np.hanning(WINDOW_WIDTH)

    # Take the FTs
    freqs, times, FT = sliding_window_fft(signal, t, hanning)

    # Convert the time and freq to a mesh (for plotting in 3d)
    F_bins, T_bins = np.meshgrid(freqs, times)

    sonogram = plt.figure("Sonogram")
    plt.contour(F_bins, T_bins, FT)
    
    return sonogram

# Create the input signal
duration = 10.0
t = np.arange(0.0, duration, 1/SAMPLE_FREQ)
signal = function_generator(t)
plt.figure()
plt.plot(t, signal)

sonogram(signal, t)

plt.show()
