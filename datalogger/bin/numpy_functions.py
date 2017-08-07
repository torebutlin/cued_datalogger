import numpy as np


def to_dB(x):
    """A simple function that converts x to dB"""
    return 20*np.log10(x)


def from_dB(x):
    """A simple function that converts x in dB to a ratio over 1"""
    return 10**(x/20)
