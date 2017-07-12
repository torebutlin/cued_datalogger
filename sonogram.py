import sys

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QSlider, QLabel, QSpinBox, QHBoxLayout
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, Qt

import numpy as np

from pyqt_matplotlib import MatplotlibCanvas

from scipy.signal import spectrogram, get_window



class SonogramPlot(MatplotlibCanvas):
    def __init__(self, sig, t, sample_freq, window_width, window_increment):
        self.sig = sig
        self.t = t
        self.sample_freq = sample_freq
        self.window_width = window_width
        self.window_increment = window_increment
        
        MatplotlibCanvas.__init__(self)
    
    def init_plot(self):
        freqs, times, self.FT = spectrogram(self.sig, self.sample_freq, 
                                            window=get_window('hann', self.window_width),
                                            noverlap=(self.window_width - self.window_increment))
        self.FT = self.FT.transpose()
        
        self.FT = np.abs(self.FT[:, :self.FT.shape[1] // 2 + 1])
        
        freqs = np.abs(freqs[:freqs.size // 2 + 1])

        self.F_bins, self.T_bins = np.meshgrid(freqs, times)
         
        self.axes.contour(self.F_bins, self.T_bins, self.FT)
        
    
    def update_plot(self, window_width):
        self.window_width = window_width
        self.init_plot()
        self.draw()


class SonogramWidget(QWidget):
    def __init__(self, sig, t, sample_freq=4096, window_width=256, window_increment=32):
        self.sig = sig
        self.t = t
        self.sample_freq = sample_freq
        self.window_width = window_width
        self.window_increment = window_increment
        
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.sonogram_plot = SonogramPlot(self.sig, self.t, self.sample_freq, self.window_width, self.window_increment)

        self.window_width_label = QLabel(self)
        self.window_width_label.setText("Window width")
        
        self.window_width_spinbox = QSpinBox(self)
        self.window_width_spinbox.setRange(2, 512)
        self.window_width_spinbox.setValue(self.window_width)
        self.window_width_spinbox.setSingleStep(64)

        
        self.window_width_slider = QSlider(Qt.Horizontal, self)
        self.window_width_slider.setFocusPolicy(Qt.NoFocus)
        self.window_width_slider.setRange(2, 512)
        self.window_width_slider.setSingleStep(64)
        self.window_width_slider.setValue(self.window_width)
        
        self.window_width_slider.valueChanged.connect(self.window_width_spinbox.setValue)
        self.window_width_spinbox.valueChanged.connect(self.window_width_slider.setValue)
        self.window_width_slider.valueChanged.connect(self.sonogram_plot.update_plot)
        self.window_width_spinbox.valueChanged.connect(self.sonogram_plot.update_plot)


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
    sig = function_generator(t)
    
    app = 0
    
    app = QApplication(sys.argv)
    sonogram = SonogramWidget(sig, t)
    sys.exit(app.exec_())  
    