import sys

from datalogger.api.numpy_extensions import to_dB
from datalogger.api.pyqt_widgets import BaseNControl, MatplotlibCanvas
from datalogger.api.pyqtgraph_extensions import ColorMapPlotWidget
from datalogger.api.toolbox import Toolbox

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QSlider, QPushButton, QLabel, QSpinBox, QHBoxLayout, QGridLayout

import numpy as np

import scipy.signal 


class MatplotlibSonogramContourWidget(MatplotlibCanvas):
    """A MatplotlibCanvas widget displaying the Sonogram contour plot"""

    def __init__(self, parent=None):
        self.parent = parent
        self.sonogram_master = self.parent.sonogram_plot

        self.parent.num_contours_slider.valueChanged.connect(self.update_plot)
        self.parent.num_contours_spinbox.valueChanged.connect(self.update_plot)
        self.parent.contour_spacing_slider.valueChanged.connect(self.update_plot)
        self.parent.contour_spacing_spinbox.valueChanged.connect(self.update_plot)

        MatplotlibCanvas.__init__(self, "Sonogram: Contour Plot")

        self.update_plot()

    def update_plot(self):
        """Redraw the sonogram on the canvas"""
        self.F_bins, self.T_bins = np.meshgrid(self.sonogram_master.freqs, self.sonogram_master.times)

        self.axes.clear()

        self.update_contour_sequence()

        self.axes.contour(self.F_bins, self.T_bins, self.sonogram_master.FT_dB, self.contour_sequence)

        self.axes.set_xlabel('Freq (Hz)')
        self.axes.set_ylabel('Time (s)')

        self.axes.set_xlim(self.sonogram_master.freqs.min(), self.sonogram_master.freqs.max())
        self.axes.set_ylim(self.sonogram_master.times.min(), self.sonogram_master.times.max())

        self.draw()

    def update_contour_sequence(self):
        """Update the array which says where to plot contours, how many etc"""
        # Create a vector with the right spacing from min to max value
        self.contour_sequence = np.arange(self.sonogram_master.FT_dB.min(), self.sonogram_master.FT_dB.max(),
                                          self.sonogram_master.contour_spacing_dB)
        # Take the appropriate number of contours
        self.contour_sequence = self.contour_sequence[-self.sonogram_master.num_contours:]


class SonogramDisplayWidget(ColorMapPlotWidget):
    """The display widget for the Sonogram in the Analysis Window"""

    def __init__(self, parent=None, sample_freq=4096, window_width=256,
                 window_overlap_fraction=8, contour_spacing_dB=5,
                 num_contours=5):
        super().__init__(parent)
        self.parent = parent

        self.sample_freq = sample_freq
        self.window_width = window_width
        self.window_overlap_fraction = window_overlap_fraction
        self.contour_spacing_dB = contour_spacing_dB
        self.num_contours = num_contours

        self.canvas.setLabel('bottom', "Frequency", "Hz")
        self.canvas.setLabel('left', "Time", "s")

        self.show()

    def update_window_width(self, value):
        self.window_width = value
        self.update_plot()
    
    def update_window_overlap_fraction(self, value):
        self.window_overlap_fraction = value
        self.update_plot()
        
    def update_contour_spacing(self, value):
        self.contour_spacing_dB = value
        self.update_plot()
        
    def update_num_contours(self, value):
        self.num_contours = value
        self.update_plot()
    

    def calculate_sonogram(self):
        """Calculate the sonogram"""

        self.freqs, self.times, self.FT = scipy.signal.spectrogram(self.sig, self.sample_freq,
                                            window=scipy.signal.get_window('hann', self.window_width),
                                            nperseg=self.window_width,
                                            noverlap=self.window_width // self.window_overlap_fraction,
                                            return_onesided=False)

        # SciPy's spectrogram gives the FT transposed, so we need to transpose it back
        self.FT = self.FT.transpose()
        # Scipy calculates all the conjugate spectra/frequencies as well -
        # we only want the positive ones
        self.freqs = np.abs(self.freqs[:self.freqs.size // 2 + 1])
        self.FT = np.abs(self.FT[:, :self.FT.shape[1] // 2 + 1])

        # Convert to dB
        self.FT_dB = to_dB(self.FT)


    def update_plot(self, data=None):
        """Recalculate, clear and replot"""

        if data is not None:
            self.sig = data
        #if self.sig is None:
            #raise ValueError("Cannot calculate sonogram: no input data")

        self.calculate_sonogram()
        self.canvas.clear()
        self.plot_colormap(self.freqs, self.times, self.FT_dB,
                           num_contours=self.num_contours,
                           contour_spacing_dB=self.contour_spacing_dB)

    def set_data(self, time_series):
        self.update_plot(time_series)
        

class SonogramToolbox(Toolbox):
    
    #sig_sonogram_control_change = pyqtSignal(name, value)
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.parent = parent

        self.sample_freq = 4096
        self.window_width = 256
        self.window_overlap_fraction = 8
        self.num_contours = 5
        self.contour_spacing_dB = 5
        
        self.init_ui()


    def init_ui(self):

        #------------Window width controls------------
        self.window_width_label = QLabel(self)
        self.window_width_label.setText("Window width")
        # Create control
        self.window_width_control = BaseNControl(Qt.Vertical, self)
        self.window_width_control.set_power_range(0, 10)
        self.window_width_control.set_value(self.window_width)
        # Update screen on change
        #self.window_width_control.valueChanged.connect(self.sig_sonogram_control_change.emit)

        #------------Window increment controls------------
        self.window_overlap_fraction_label = QLabel(self)
        self.window_overlap_fraction_label.setText("Window overlap fraction")
        # Create control
        self.window_overlap_fraction_control = BaseNControl(Qt.Vertical, self)
        self.window_overlap_fraction_control.set_power_range(0, 6)
        self.window_overlap_fraction_control.set_value(self.window_overlap_fraction)
        # Update screen on change
        #self.window_overlap_fraction_control.valueChanged.connect(self.sig_sonogram_control_change.emit)

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
        self.contour_spacing_spinbox.setValue(self.contour_spacing_dB)
        self.contour_spacing_slider.setValue(self.contour_spacing_dB)
        # Update screen on change
        #self.contour_spacing_slider.valueChanged.connect(self.sig_sonogram_control_change.emit)
        #self.contour_spacing_spinbox.valueChanged.connect(self.sig_sonogram_control_change.emit)

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
        self.num_contours_spinbox.setValue(self.num_contours)
        self.num_contours_slider.setValue(self.num_contours)
        # Update screen on change
        #self.num_contours_slider.valueChanged.connect(self.sig_sonogram_control_change.emit)
        #self.num_contours_spinbox.valueChanged.connect(self.sig_sonogram_control_change.emit)

        #------------Matplotlib window controls---------
        # Create button
        self.convert_to_contour_btn = QPushButton("Convert to contour plot", self)
        self.convert_to_contour_btn.resize(self.convert_to_contour_btn.sizeHint())
        self.convert_to_contour_btn.clicked.connect(self.open_contour_plot)

        #------------Layout------------
        # Sonogram controls:
        self.sonogram_controls_tab = QWidget(self)

        sonogram_controls_layout = QGridLayout()
        sonogram_controls_layout.addWidget(self.window_width_label, 0, 0)
        sonogram_controls_layout.addWidget(self.window_width_control, 1, 0)
        sonogram_controls_layout.addWidget(self.window_overlap_fraction_label, 0, 1)
        sonogram_controls_layout.addWidget(self.window_overlap_fraction_control, 1, 1)
        
        self.sonogram_controls_tab.setLayout(sonogram_controls_layout)

        # Plot controls:
        self.plot_controls_tab = QWidget(self)

        plot_controls_layout = QGridLayout()
        plot_controls_layout.addWidget(self.contour_spacing_label, 1, 0)
        plot_controls_layout.addWidget(self.contour_spacing_spinbox, 2, 0)
        plot_controls_layout.addWidget(self.contour_spacing_slider, 3, 0)
        plot_controls_layout.addWidget(self.num_contours_label, 1, 1)
        plot_controls_layout.addWidget(self.num_contours_spinbox, 2, 1)
        plot_controls_layout.addWidget(self.num_contours_slider, 3, 1)
        
        self.plot_controls_tab.setLayout(plot_controls_layout)
        
        # Export:
        self.export_tab = QWidget(self)
        
        export_layout = QVBoxLayout()
        export_layout.addWidget(self.convert_to_contour_btn)
        
        self.export_tab.setLayout(export_layout)        

        self.addTab(self.plot_controls_tab, "Plot Controls")
        self.addTab(self.sonogram_controls_tab, "Sonogram Controls")
        self.addTab(self.export_tab, "Export")

    def open_contour_plot(self):
        if hasattr(self, 'contour_plot'):
            self.contour_plot.close()

        self.contour_plot = MatplotlibSonogramContourWidget(self)
        self.contour_plot.show()


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
    
    w = QWidget()
    
    hbox = QHBoxLayout()
    w.setLayout(hbox)
    
    toolbox = SonogramToolbox(w)
    displaywidget = SonogramDisplayWidget()
    displaywidget.update_plot(sig)
   
    hbox.addWidget(toolbox)
    hbox.addWidget(displaywidget)
    
    toolbox.contour_spacing_slider.valueChanged.connect(displaywidget.update_contour_spacing)
    toolbox.contour_spacing_spinbox.valueChanged.connect(displaywidget.update_contour_spacing)
    
    toolbox.num_contours_slider.valueChanged.connect(displaywidget.update_num_contours)
    toolbox.num_contours_spinbox.valueChanged.connect(displaywidget.update_num_contours)
    
    toolbox.window_overlap_fraction_control.valueChanged.connect(displaywidget.update_window_overlap_fraction)
    
    toolbox.window_width_control.valueChanged.connect(displaywidget.update_window_width)

    w.show()
    
    sys.exit(app.exec_())

