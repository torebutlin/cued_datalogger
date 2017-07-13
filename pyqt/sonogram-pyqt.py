import sys

from PyQt5 import QtCore
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QSlider, QLabel, QSpinBox, QHBoxLayout, QGridLayout, QComboBox
from mypyqt_widgets import Power2SteppedSlider, Power2SteppedSpinBox

import pyqtgraph as pg
from pyqtgraph import PlotWidget, PlotItem
from mypyqtgraph_functions import ContourMap

import numpy as np

from scipy.signal import spectrogram, get_window


class SonogramPlotPyQt(QWidget):
    def __init__(self, sig, t, sample_freq, window_width, window_increment,
                 plot_type="Contour", num_contours=32, contour_spacing=1e-3, cmap="jet"):
        self.sig = sig
        self.t = t
        self.sample_freq = sample_freq
        self.window_width = window_width
        self.window_increment = window_increment
        self.plot_type = plot_type
        self.num_contours = num_contours
        self.contour_spacing = contour_spacing
        self.cmap = cmap
                  
        super().__init__()
        
        self.recalculate_sonogram()
        
        # Convert the sonogram data to contours
        self.contour_map = ContourMap(self.freqs, self.times, self.FT, num_contours, contour_spacing, cmap)
        self.contour_map.setLabel('bottom', "Frequency", "Hz")
        self.contour_map.setLabel('left', "Time", "s")
        
        # Show the contour map widget
        vbox = QVBoxLayout()
        vbox.addWidget(self.contour_map)
        self.setLayout(vbox)
        
    
    def recalculate_sonogram(self):
        self.freqs, self.times, self.FT = spectrogram(self.sig, self.sample_freq,
                                                      window=get_window('hann', self.window_width), 
                                                      nperseg=self.window_width, 
                                                      noverlap=(self.window_width - self.window_increment))
        # SciPy's spectrogram gives the FT transposed, so we need to transpose it back
        self.FT = self.FT.transpose()
        # Take the real part of the spectrum
        self.FT = np.abs(self.FT[:, :self.FT.shape[1] // 2 + 1])
        self.freqs = np.abs(self.freqs[:self.freqs.size // 2 + 1])
        
        
        
    def draw_plot(self):      
        if self.plot_type == "Contour":
            self.contour_map.update_contours()
            
        elif self.plot_type == "Surface":
            pass
        
        elif self.plot_type == "Colourmap":
            pass
            
        else:
            pass
                
    
    def update_plot(self, value):
        sender_name = self.sender().objectName()
        
        if sender_name == "window_width_spinbox" or sender_name == "window_width_slider":
            self.window_width = value
           
        elif sender_name == "window_increment_spinbox" or sender_name == "window_increment_slider":
            self.window_increment = value
            
        elif sender_name == "sample_freq_spinbox" or sender_name == "sample_freq_slider":
            self.sample_freq = value
        
        elif sender_name == "plot_type_combobox":
            self.plot_type = value
        
        else:
            pass
        
        self.recalculate_sonogram()
        
        # Update the plot's data as well
        self.contour_map.x = self.freqs
        self.contour_map.y = self.times
        self.contour_map.Z = self.FT
        self.contour_map.num_contours = self.num_contours
        self.contour_map.contour_spacing = self.contour_spacing
        self.contour_map.cmap_name = self.cmap
        self.contour_map.update_scale_fact()
        
        self.draw_plot()
        

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
        self.sonogram_plot_pyqt = SonogramPlotPyQt(self.sig, self.t, self.sample_freq, self.window_width, self.window_increment)

        ## Window width interactivity
        self.window_width_label = QLabel(self)
        self.window_width_label.setText("Window width")
        # Create spinbox
        self.window_width_spinbox = Power2SteppedSpinBox(self)
        self.window_width_spinbox.setObjectName("window_width_spinbox")
        self.window_width_spinbox.setRange(16, 512)
        # Create slider
        self.window_width_slider = Power2SteppedSlider(Qt.Horizontal, self)
        self.window_width_slider.setObjectName("window_width_slider")
        self.window_width_slider.setRange(16, 512)
        # Connect spinbox and slider together
        self.window_width_spinbox.valueChanged.connect(self.window_width_slider.setValue)
        self.window_width_slider.valueChanged.connect(self.window_width_spinbox.setValue)
        # Set values
        self.window_width_spinbox.setValue(self.window_width)
        self.window_width_slider.setValue(self.window_width)
        # Update screen on change
        self.window_width_slider.valueChanged.connect(self.sonogram_plot_pyqt.update_plot)
        self.window_width_spinbox.valueChanged.connect(self.sonogram_plot_pyqt.update_plot)
        
        ## Window increment interactivity
        self.window_increment_label = QLabel(self)
        self.window_increment_label.setText("Window increment")
        # Create spinbox       
        self.window_increment_spinbox = Power2SteppedSpinBox(self)
        self.window_increment_spinbox.setObjectName("window_increment_spinbox")        
        self.window_increment_spinbox.setRange(2, 256)
        # Create slider        
        self.window_increment_slider = Power2SteppedSlider(Qt.Horizontal, self)
        self.window_increment_slider.setObjectName("window_increment_slider")
        self.window_increment_slider.setRange(16, 512)
        # Connect spinbox and slider together
        self.window_increment_spinbox.valueChanged.connect(self.window_increment_slider.setValue)
        self.window_increment_slider.valueChanged.connect(self.window_increment_spinbox.setValue)
        # Set values
        self.window_increment_spinbox.setValue(self.window_increment)
        self.window_increment_slider.setValue(self.window_increment)
        # Update screen on change
        self.window_increment_slider.valueChanged.connect(self.sonogram_plot_pyqt.update_plot)
        self.window_increment_spinbox.valueChanged.connect(self.sonogram_plot_pyqt.update_plot)
        
        ## Sample freq interactivity
        self.sample_freq_label = QLabel(self)
        self.sample_freq_label.setText("Sample freq")
        # Create spinbox       
        self.sample_freq_spinbox = Power2SteppedSpinBox(self)
        self.sample_freq_spinbox.setObjectName("sample_freq_spinbox")        
        self.sample_freq_spinbox.setRange(2, 256)
        # Create slider        
        self.sample_freq_slider = Power2SteppedSlider(Qt.Horizontal, self)
        self.sample_freq_slider.setObjectName("sample_freq_slider")
        self.sample_freq_slider.setRange(16, 512)
        # Connect spinbox and slider together
        self.sample_freq_spinbox.valueChanged.connect(self.sample_freq_slider.setValue)
        self.sample_freq_slider.valueChanged.connect(self.sample_freq_spinbox.setValue)
        # Set values
        self.sample_freq_spinbox.setValue(self.sample_freq)
        self.sample_freq_slider.setValue(self.sample_freq)
        # Update screen on change
        self.sample_freq_slider.valueChanged.connect(self.sonogram_plot_pyqt.update_plot)
        self.sample_freq_spinbox.valueChanged.connect(self.sonogram_plot_pyqt.update_plot)
        
        ## Plot type interactivity
        self.plot_type_label = QLabel(self)
        self.plot_type_label.setText("Plot type")
        # Create combobox
        self.plot_type_combobox = QComboBox(self)
        self.plot_type_combobox.addItems(["Contour", "Surface", "Colourmap"])
        self.plot_type_combobox.setObjectName("plot_type_combobox")
        # Update on change
        self.plot_type_combobox.activated[str].connect(self.sonogram_plot_pyqt.update_plot)        
        
        # Layout
        grid = QGridLayout()
        grid.addWidget(self.window_width_label, 0, 0)
        grid.addWidget(self.window_width_spinbox, 0, 1)
        grid.addWidget(self.window_width_slider, 0, 2)
        grid.addWidget(self.window_increment_label, 1, 0)
        grid.addWidget(self.window_increment_spinbox, 1, 1)
        grid.addWidget(self.window_increment_slider, 1, 2)
        grid.addWidget(self.sample_freq_label, 2, 0)
        grid.addWidget(self.sample_freq_spinbox, 2, 1)
        grid.addWidget(self.sample_freq_slider, 2, 2)
        grid.addWidget(self.plot_type_label, 3, 0)
        grid.addWidget(self.plot_type_combobox, 3, 1)
        
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        
        hbox.addWidget(self.sonogram_plot_pyqt)
        
        vbox.addLayout(hbox)
        vbox.addLayout(grid)

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
    