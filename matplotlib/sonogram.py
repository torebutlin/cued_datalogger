import sys

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QSlider, QLabel, QSpinBox, QHBoxLayout, QGridLayout, QComboBox
from mypyqt_widgets import Power2SteppedSlider, Power2SteppedSpinBox
from pyqt_matplotlib import MatplotlibCanvas

import numpy as np
from mynumpy_functions import to_dB, from_dB

from scipy.signal import spectrogram, get_window


class SonogramPlotWidget(MatplotlibCanvas):
    """A MatplotlibCanvas widget displaying the Sonogram plot"""
    
    def __init__(self, sig, t, sample_freq, window_width, window_increment,
                 plot_type="Colourmap", num_contours=5, contour_spacing_dB=5):
        self.sig = sig
        self.t = t
        self.sample_freq = sample_freq
        self.window_width = window_width
        self.window_increment = window_increment
        self.plot_type = plot_type
        self.num_contours = num_contours
        self.contour_spacing_dB = contour_spacing_dB
        
        MatplotlibCanvas.__init__(self, "Sonogram")

        
        # Calculate the initial sonogram and display it
        self.calculate_sonogram()
        self.draw_plot()
    
    def draw_plot(self):
        """Redraw the sonogram on the canvas"""
        
        self.axes.clear()
        
        if self.plot_type == "Contour":
            
            self.update_contour_sequence()
            
            self.axes.contour(self.F_bins, self.T_bins, self.FT_dB, self.contour_sequence)
            
            self.axes.set_xlabel('Freq (Hz)')
            self.axes.set_ylabel('Time (s)')
            
            self.axes.set_xlim(self.freqs.min(), self.freqs.max())
            self.axes.set_ylim(self.times.min(), self.times.max())
            
        elif self.plot_type == "Surface":
            pass
        
        elif self.plot_type == "Colourmap":
            
            self.update_contour_sequence()
            
            self.axes.pcolormesh(self.F_bins, self.T_bins, self.FT_dB, vmin=self.contour_sequence[0])
            
            self.axes.set_xlabel('Freq (Hz)')
            self.axes.set_ylabel('Time (s)')
            
            self.axes.set_xlim(self.freqs.min(), self.freqs.max())
            self.axes.set_ylim(self.times.min(), self.times.max())
            
        else:
            pass
        
        self.draw()
        
    def update_attributes(self, value):
        """A slot for updating the attributes when input widgets are adjusted"""
        
        # What sent the signal?
        sender_name = self.sender().objectName()
        
        if sender_name == "window_width_spinbox" or sender_name == "window_width_slider":
            self.window_width = value
           
        elif sender_name == "window_increment_spinbox" or sender_name == "window_increment_slider":
            self.window_increment = value
            
        elif sender_name == "sample_freq_spinbox" or sender_name == "sample_freq_slider":
            self.sample_freq = value
        
        elif sender_name == "plot_type_combobox":
            self.plot_type = value
        
        elif sender_name == "contour_spacing_spinbox" or sender_name == "contour_spacing_slider":
            self.contour_spacing_dB = value
            
        elif sender_name == "num_contours_spinbox" or sender_name == "num_contours_slider":
            self.num_contours = value
        
        else:
            print("Sender {} not implemented.".format(sender_name))
            # Discard any other signal
            pass
        
        # Update the plot
        self.calculate_sonogram()
        self.draw_plot()
    
    def calculate_sonogram(self):
        """Recalculate the sonogram"""
        #TODO: In reality, get rid of this - just for demos
        self.t = np.arange(0.0, 10, 1/self.sample_freq)
        self.sig = function_generator(self.t)
        #
        
        self.freqs, self.times, self.FT = spectrogram(self.sig, self.sample_freq, 
                                            window=get_window('hann', self.window_width),
                                            nperseg=self.window_width,
                                            noverlap=(self.window_width - self.window_increment))
        
        # SciPy's spectrogram gives the FT transposed, so we need to transpose it back
        self.FT = self.FT.transpose()
        # Scipy calculates all the conjugate spectra/frequencies as well -
        # we only want the positive ones
        # TODO: This might create problems if only real data is input, as scipy might
        # calculate single-sided spectra if the data is solely real.
        self.freqs = np.abs(self.freqs[:self.freqs.size // 2 + 1])
        self.FT = np.abs(self.FT[:, :self.FT.shape[1] // 2 + 1])
        
        # Convert to dB
        self.FT_dB = to_dB(self.FT)
        
        # Create mesh for plotting in 3D
        self.F_bins, self.T_bins = np.meshgrid(self.freqs, self.times)

    
    def update_contour_sequence(self):
        """Update the array which says where to plot contours, how many etc"""
        # Create a vector with the right spacing from min to max value
        self.contour_sequence = np.arange(self.FT_dB.min(), self.FT_dB.max(),
                                          self.contour_spacing_dB)
        # Take the appropriate number of contours
        self.contour_sequence = self.contour_sequence[-self.num_contours:]
        


class SonogramWidget(QWidget):
    def __init__(self, sig, t, sample_freq=4096, window_width=256, window_increment=32, parent=None):
        self.sig = sig
        self.t = t
        self.sample_freq = sample_freq
        self.window_width = window_width
        self.window_increment = window_increment
               
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        # Add a sonogram plot
        self.sonogram_plot = SonogramPlotWidget(self.sig, self.t, self.sample_freq, self.window_width, self.window_increment)
        
        #------------Window width controls------------
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
        self.window_width_slider.valueChanged.connect(self.sonogram_plot.update_attributes)
        self.window_width_spinbox.valueChanged.connect(self.sonogram_plot.update_attributes)
        
        #------------Window increment controls------------
        self.window_increment_label = QLabel(self)
        self.window_increment_label.setText("Window increment")
        # Create spinbox       
        self.window_increment_spinbox = Power2SteppedSpinBox(self)
        self.window_increment_spinbox.setObjectName("window_increment_spinbox")        
        self.window_increment_spinbox.setRange(16, 256)
        # Create slider        
        self.window_increment_slider = Power2SteppedSlider(Qt.Horizontal, self)
        self.window_increment_slider.setObjectName("window_increment_slider")
        self.window_increment_slider.setRange(16, 256)
        # Connect spinbox and slider together
        self.window_increment_spinbox.valueChanged.connect(self.window_increment_slider.setValue)
        self.window_increment_slider.valueChanged.connect(self.window_increment_spinbox.setValue)
        # Set values
        self.window_increment_spinbox.setValue(self.window_increment)
        self.window_increment_slider.setValue(self.window_increment)
        # Update screen on change
        self.window_increment_slider.valueChanged.connect(self.sonogram_plot.update_attributes)
        self.window_increment_spinbox.valueChanged.connect(self.sonogram_plot.update_attributes)
        
        #------------Sample freq controls------------
        self.sample_freq_label = QLabel(self)
        self.sample_freq_label.setText("Sample freq")
        # Create spinbox       
        self.sample_freq_spinbox = Power2SteppedSpinBox(self)
        self.sample_freq_spinbox.setObjectName("sample_freq_spinbox")        
        self.sample_freq_spinbox.setRange(256, 32768)
        # Create slider        
        self.sample_freq_slider = Power2SteppedSlider(Qt.Horizontal, self)
        self.sample_freq_slider.setObjectName("sample_freq_slider")
        self.sample_freq_slider.setRange(256, 32768)
        # Connect spinbox and slider together
        self.sample_freq_spinbox.valueChanged.connect(self.sample_freq_slider.setValue)
        self.sample_freq_slider.valueChanged.connect(self.sample_freq_spinbox.setValue)
        # Set values
        self.sample_freq_spinbox.setValue(self.sample_freq)
        self.sample_freq_slider.setValue(self.sample_freq)
        # Update screen on change
        self.sample_freq_slider.valueChanged.connect(self.sonogram_plot.update_attributes)
        self.sample_freq_spinbox.valueChanged.connect(self.sonogram_plot.update_attributes)
        
        #------------Plot type controls------------
        self.plot_type_label = QLabel(self)
        self.plot_type_label.setText("Plot type")
        # Create combobox
        self.plot_type_combobox = QComboBox(self)
        self.plot_type_combobox.addItems(["Colourmap", "Contour", "Surface"])
        self.plot_type_combobox.setObjectName("plot_type_combobox")
        # Update on change
        self.plot_type_combobox.activated[str].connect(self.sonogram_plot.update_attributes)        
        
        #------------Contour spacing controls------------
        self.contour_spacing_label = QLabel(self)
        self.contour_spacing_label.setText("Contour spacing")
        # Create spinbox       
        self.contour_spacing_spinbox = QSpinBox(self)
        self.contour_spacing_spinbox.setObjectName("contour_spacing_spinbox")        
        self.contour_spacing_spinbox.setRange(1, 12)
        # Create slider        
        self.contour_spacing_slider = QSlider(Qt.Vertical, self)
        self.contour_spacing_slider.setObjectName("contour_spacing_slider")
        self.contour_spacing_slider.setRange(1, 12)
        # Connect spinbox and slider together
        self.contour_spacing_spinbox.valueChanged.connect(self.contour_spacing_slider.setValue)
        self.contour_spacing_slider.valueChanged.connect(self.contour_spacing_spinbox.setValue)
        # Set values
        self.contour_spacing_spinbox.setValue(self.sonogram_plot.contour_spacing_dB)
        self.contour_spacing_slider.setValue(self.sonogram_plot.contour_spacing_dB)
        # Update screen on change
        self.contour_spacing_slider.valueChanged.connect(self.sonogram_plot.update_attributes)
        self.contour_spacing_spinbox.valueChanged.connect(self.sonogram_plot.update_attributes)
        
        #------------Num contours controls------------
        self.num_contours_label = QLabel(self)
        self.num_contours_label.setText("Num contours")
        # Create spinbox       
        self.num_contours_spinbox = QSpinBox(self)
        self.num_contours_spinbox.setObjectName("num_contours_spinbox")        
        self.num_contours_spinbox.setRange(1, 12)
        # Create slider        
        self.num_contours_slider = QSlider(Qt.Vertical, self)
        self.num_contours_slider.setObjectName("num_contours_slider")
        self.num_contours_slider.setRange(1, 12)
        # Connect spinbox and slider together
        self.num_contours_spinbox.valueChanged.connect(self.num_contours_slider.setValue)
        self.num_contours_slider.valueChanged.connect(self.num_contours_spinbox.setValue)
        # Set values
        self.num_contours_spinbox.setValue(self.sonogram_plot.num_contours)
        self.num_contours_slider.setValue(self.sonogram_plot.num_contours)
        # Update screen on change
        self.num_contours_slider.valueChanged.connect(self.sonogram_plot.update_attributes)
        self.num_contours_spinbox.valueChanged.connect(self.sonogram_plot.update_attributes)
        
        #------------Layout------------
        # Sonogram controls:
        self.sonogram_controls_label = QLabel(self)
        self.sonogram_controls_label.setText("<b>Sonogram controls</b>")
        
        sonogram_controls = QGridLayout()
        sonogram_controls.addWidget(self.sonogram_controls_label, 0, 0)
        sonogram_controls.addWidget(self.window_width_label, 1, 0)
        sonogram_controls.addWidget(self.window_width_spinbox, 1, 1)
        sonogram_controls.addWidget(self.window_width_slider, 1, 2)
        sonogram_controls.addWidget(self.window_increment_label, 2, 0)
        sonogram_controls.addWidget(self.window_increment_spinbox, 2, 1)
        sonogram_controls.addWidget(self.window_increment_slider, 2, 2)
        sonogram_controls.addWidget(self.sample_freq_label, 3, 0)
        sonogram_controls.addWidget(self.sample_freq_spinbox, 3, 1)
        sonogram_controls.addWidget(self.sample_freq_slider, 3, 2)
        
        # Plot controls:
        self.plot_controls_label = QLabel(self)
        self.plot_controls_label.setText("<b>Plot controls</b>")
        
        plot_controls = QGridLayout()
        plot_controls.addWidget(self.plot_controls_label, 0, 0)
        plot_controls.addWidget(self.contour_spacing_label, 1, 0)
        plot_controls.addWidget(self.contour_spacing_spinbox, 2, 0)
        plot_controls.addWidget(self.contour_spacing_slider, 3, 0)
        plot_controls.addWidget(self.num_contours_label, 1, 1)
        plot_controls.addWidget(self.num_contours_spinbox, 2, 1)
        plot_controls.addWidget(self.num_contours_slider, 3, 1)
        plot_controls.addWidget(self.plot_type_label, 4, 0)
        plot_controls.addWidget(self.plot_type_combobox, 4, 1)
                
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        
        hbox.addWidget(self.sonogram_plot)
        hbox.addLayout(plot_controls)
        
        vbox.addLayout(hbox)
        vbox.addLayout(sonogram_controls)

        self.setLayout(vbox)
        self.setWindowTitle('Sonogram')
        self.show()


def func_1(t, w, x, A=4e3):
    """A simple decaying sine wave function."""
    return A * np.exp((1j*w - x)*t)


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
    