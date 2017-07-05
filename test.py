# -*- coding: utf-8 -*-
"""
Created on Wed Jul  5 15:19:54 2017

@author: theo
"""

import numpy as np
import matplotlib.pyplot as plt
from time import sleep

def wave(k, x, w, t):
    return np.exp(1j*(k*x - w*t))


def update_fig(x, y):
    plt.clf()
    plt.plot(x, y)
    plt.show()

t = np.linspace(0, 5, 1e3)
x = np.linspace(0, 100, 1e3)

fig = plt.figure()

for i in np.arange(0, 20):
    print(i)
    f = wave(i, x, 50*2*np.pi, t)
    update_fig(t, f)
    sleep(1)
    plt.show()
