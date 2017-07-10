from numpy.fft import rfft, rfftfreq
import numpy as np
import matplotlib.pyplot as plt

SAMPLE_FREQ = 4096
WINDOW_WIDTH = 256
WINDOW_INCREMENT = 32


def func_1(t, w, x, k=0):
    return np.exp((1j*w - x)*t)


def function_generator(t):
    f1 = func_1(t, 2000*2*np.pi, 2)
    f2 = func_1(t, 500*2*np.pi, 1)
    f1[np.floor(f1.size/2):] += f1[:np.floor(f1.size/2)]
    result = f1 + f2
    return result


duration = 10.0
t = np.arange(0.0, duration, 1/SAMPLE_FREQ)
signal = function_generator(t)
plt.figure()
plt.plot(t, signal)

hanning = np.hanning(WINDOW_WIDTH)

num_windows = np.floor(signal.size / WINDOW_INCREMENT)

FT = np.zeros((num_windows, WINDOW_WIDTH/2 + 1))

times = np.linspace(0, t[-1], num=num_windows)
freqs = rfftfreq(WINDOW_WIDTH, 1/SAMPLE_FREQ)

F_bins, T_bins = np.meshgrid(freqs, times)

signal_extended = np.append(np.zeros(int(WINDOW_WIDTH/2)), signal)
signal_extended = np.append(signal_extended, np.zeros(int(WINDOW_WIDTH/2)))

for i in np.arange(num_windows):
    lower = i * WINDOW_INCREMENT
    upper = lower + WINDOW_WIDTH

    window = np.multiply(signal_extended[lower:upper], hanning)

    FT[i] = np.abs(rfft(window))

plt.figure()
plt.contour(F_bins, T_bins, FT)
plt.show()
