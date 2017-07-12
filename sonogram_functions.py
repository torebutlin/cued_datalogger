from numpy.fft import rfft, rfftfreq
import numpy as np


def window_fft(signal, window_lower, window_upper, window_shape):
    """Takes the FT of a window within a signal, scaled by a shape array."""
    window = np.multiply(signal[window_lower:window_upper], window_shape)

    return np.abs(rfft(window))


def calculate_sonogram(signal, t, sample_freq, window_width, window_increment): 
    
    num_windows = signal.size // window_increment

    # Create the array to store the FT results in
    FT = np.zeros((num_windows, window_width//2 + 1))

    # Find the associated time vector and frequencies for the FT
    times = np.linspace(0, t[-1], num=num_windows)
    freqs = rfftfreq(window_width, 1/sample_freq)
    # Convert the time and freq to a mesh (for plotting in 3d)
    F_bins, T_bins = np.meshgrid(freqs, times)

    # Extend the signal so that the window can be slid off the ends
    signal_extended = np.append(np.zeros(window_width//2), signal)
    signal_extended = np.append(signal_extended, np.zeros(window_width//2))

    # Iterate through the signal taking FTs of each window
    for i in np.arange(num_windows):
        lower = i * window_increment
        upper = lower + window_width

        FT[i] = window_fft(signal_extended, lower, upper, np.hanning(window_width))

    
    return F_bins, T_bins, FT


        