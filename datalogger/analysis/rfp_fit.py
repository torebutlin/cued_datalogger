import sys

if __name__ == '__main__':
    sys.path.append('../')

from bin.channel import ChannelSet
from bin.file_import import import_from_mat
from bin.numpy_functions import circle_fit, to_dB

from PyQt5.QtCore import Qt
from PyQt5 import QtGui
from PyQt5.QtWidgets import (QApplication, QWidget, QGridLayout, QTableWidget,
                             QDoubleSpinBox, QCheckBox, QPushButton, QGroupBox,
                             QVBoxLayout, QHBoxLayout, QLabel, QComboBox)

import numpy as np
from scipy.optimize import curve_fit

from pyqtgraph.Qt import QtCore
import pyqtgraph as pg
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
pg.setConfigOption('antialias', True)
defaultpen = pg.mkPen('k')
import matplotlib.pyplot as plt

def sdof_modal_peak(w, wr, zr, cr, phi):
    return cr*np.exp(1j*phi) / (wr**2 - w**2 + 2j * zr * wr**2)


def iw_polynomial(w, coefficients):
    order = coefficients.size

    y = np.zeros_like(w, dtype='complex128')

    for i in np.arange(order):
        k = order - i
        y += coefficients[i] * (1j*w)**k

    return y


def rfp_fit(w, a_coeffs, b_coeffs):
    rfp = iw_polynomial(w, a_coeffs) / iw_polynomial(w, b_coeffs)
    return np.real(np.append(rfp.real, rfp.imag))


w = np.linspace(0, 25, 1e4)

frf = sdof_modal_peak(w, 5, 0.006, 8e12, np.pi/2) \
        + sdof_modal_peak(w, 10, 0.008, 8e12, 0) \
        + sdof_modal_peak(w, 12, 0.003, 8e12, 0) \
        + sdof_modal_peak(w, 20, 0.01, 22e12, 0)

popts, pconv = curve_fit(rfp_fit, w, np.real(np.append(frf.real, frf.imag)), p0=[[1], [1]])

plt.plot(w, iw_polynomial(w, popts[0]) / iw_polynomial(w, popts[1]))