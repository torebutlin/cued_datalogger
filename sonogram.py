"""
Sonogram
Author: Theo Brown (tab53)
"""

import numpy as np
import matplotlib.pyplot as plt


def source_function(t, f=100, x=5):
    return np.exp((1j * f*2*np.pi - x) * t)


t = np.arange(0, 1, 0.0001)  # Create time range
y = source_function(t)      # Create data

plt.plot(t, y)
plt.show()

