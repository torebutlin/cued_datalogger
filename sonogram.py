import sys

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QSlider, QLabel, QSpinBox, QHBoxLayout
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, Qt

import numpy as np
from numpy.fft import rfft, rfftfreq

from pyqt_matplotlib import MatplotlibCanvas

from sonogram_functions import sliding_window_fft


class SonogramPlot(MatplotlibCanvas):
    def __init__(self, signal, t, sample_freq, window_width, window_increment):
        self.signal = signal
        self.t = t
        self.sample_freq = sample_freq
        self.window_width = window_width
        self.window_increment = window_increment
        
        MatplotlibCanvas.__init__(self)
    
    def init_plot(self):
        # Create the window
        hanning = np.hanning(self.window_width)

        # Take the FTs
        freqs, times, FT = sliding_window_fft(self.signal, self.t, hanning, 
                                              self.sample_freq, self.window_width, 
                                              self.window_increment)

        # Convert the time and freq to a mesh (for plotting in 3d)
        F_bins, T_bins = np.meshgrid(freqs, times)

        self.axes.contour(F_bins, T_bins, FT)


class SonogramWidget(QWidget):
    def __init__(self, signal, t, sample_freq=4096, window_width=356, window_increment=32):
        self.signal = signal
        self.t = t
        self.sample_freq = sample_freq
        self.window_width = window_width
        self.window_increment = window_increment
        
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.sonogram_plot = SonogramPlot(self.signal, self.t, self.sample_freq, self.window_width, self.window_increment)

        self.window_width_label = QLabel(self)
        self.window_width_label.setText("Window width")
        
        self.window_width_spinbox = QSpinBox(self)
        self.window_width_spinbox.setRange(2, 1024)
        self.window_width_spinbox.setValue(256)

        
        self.window_width_slider = QSlider(Qt.Horizontal, self)
        self.window_width_slider.setFocusPolicy(Qt.NoFocus)
        self.window_width_slider.setRange(2, 1024)
        self.window_width_slider.setValue(256)
        
        self.window_width_slider.valueChanged.connect(self.window_width_spinbox.setValue)
        self.window_width_spinbox.valueChanged.connect(self.window_width_slider.setValue)
        

        hbox = QHBoxLayout()
        hbox.addWidget(self.window_width_label)
        hbox.addWidget(self.window_width_spinbox)
        hbox.addWidget(self.window_width_slider)  
        
        vbox = QVBoxLayout()
        vbox.addWidget(self.sonogram_plot)
        vbox.addLayout(hbox)

        self.setLayout(vbox)
        self.setWindowTitle('Sonogram')
        self.show()


def func_1(t, w, x, k=0):
    """A simple decaying sine wave function."""
    return np.exp((1j*w - x)*t)


def function_generator(t):
    """A simple function generator with echoes."""
    f1 = func_1(t, 2000*2*np.pi, 2)
    f2 = func_1(t, 500*2*np.pi, 1)
    # Create an echo of one of the functions
    f1[f1.size//2:] += f1[:f1.size//2]
    result = f1 + f2
    return result


if __name__ == '__main__':
    duration = 10.0
    t = np.arange(0.0, duration, 1/4096)
    signal = function_generator(t)
    
    app = QApplication(sys.argv)
    sonogram = SonogramWidget(signal, t)
    sys.exit(app.exec_())  
    