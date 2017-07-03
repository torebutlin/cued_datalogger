"""
Sonogram
Author: Theo Brown (tab53)
"""

import numpy as np
import matplotlib.pyplot as plt


sample_freq = 200


def source_function(t, x=10):
    return np.exp((1j * sample_freq*2*np.pi - x) * t)


def to_db(x):
    return 20*np.log10(x)


# Create time range
t = np.arange(0, 2.5, 0.0001)
# Create data
y = source_function(t)

# Plot data
plt.plot(t, y)
# plt.show()

# Take FFT of data
sp = np.fft.fft(y)

# Plot FFT
plt.magnitude_spectrum(y, Fs=sample_freq, scale='dB')
plt.show()

# Plot spectrogram
plt.specgram(y, Fs=sample_freq)
plt.show()
