import sys
if __name__ == '__main__':
    sys.path.append('../bin')
    from numpy_functions import to_dB
    from pyqt_widgets import Power2SteppedSlider, Power2SteppedSpinBox, ColorMapPlotWidget, MatplotlibCanvas
else:
    from datalogger.bin.numpy_functions import to_dB
    from datalogger.bin.pyqt_widgets import Power2SteppedSlider, Power2SteppedSpinBox, ColorMapPlotWidget, MatplotlibCanvas

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QSlider, QPushButton, QLabel, QSpinBox, QHBoxLayout, QGridLayout

import numpy as np

from scipy.signal import spectrogram, get_window


class SonogramContourWidget(MatplotlibCanvas):
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


class SonogramPlotWidget(ColorMapPlotWidget):
    """A widget displaying the Sonogram colourmap plot"""

    def __init__(self, sample_freq=4096, window_width=256,
                 window_overlap_fraction=8, contour_spacing_dB=5,
                 num_contours=5, parent=None):
        super().__init__()
        self.parent = parent

        self.sample_freq = sample_freq
        self.window_width = window_width
        self.window_overlap_fraction = window_overlap_fraction
        self.contour_spacing_dB = contour_spacing_dB
        self.num_contours = num_contours

        self.setLabel('bottom', "Frequency", "Hz")
        self.setLabel('left', "Time", "s")

        self.show()


    def update_attributes(self, value):
        """A slot for updating the attributes when input widgets are adjusted"""

        # What sent the signal?
        sender_name = self.sender().objectName()

        if sender_name == "window_width_spinbox" or sender_name == "window_width_slider":
            self.window_width = value

        elif sender_name == "window_overlap_fraction_spinbox" or sender_name == "window_overlap_fraction_slider":
            self.window_overlap_fraction = value

        elif sender_name == "contour_spacing_spinbox" or sender_name == "contour_spacing_slider":
            self.contour_spacing_dB = value

        elif sender_name == "num_contours_spinbox" or sender_name == "num_contours_slider":
            self.num_contours = value

        else:
            print("Sender {} not implemented.".format(sender_name))
            # Discard any other signal
            pass

        # Update the plot
        self.update_plot()

    def calculate_sonogram(self):
        """Calculate the sonogram"""

        self.freqs, self.times, self.FT = spectrogram(self.sig, self.sample_freq,
                                            window=get_window('hann', self.window_width),
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


    def update_plot(self, sig=None):
        """Recalculate, clear and replot"""

        if sig is not None:
            self.sig = sig
        if self.sig == None:
            raise ValueError("Cannot calculate sonogram: no input data")

        self.calculate_sonogram()
        self.clear()
        self.plot_colormap(self.freqs, self.times, self.FT_dB,
                           num_contours=self.num_contours,
                           contour_spacing_dB=self.contour_spacing_dB)


class SonogramWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()

        self.sample_freq = 4096
        self.window_width = 256
        self.window_overlap_fraction = 8

        self.init_ui()

    def init_ui(self):
        # Add a sonogram plot
        self.sonogram_plot = SonogramPlotWidget(parent=self)

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
        self.window_overlap_fraction_label = QLabel(self)
        self.window_overlap_fraction_label.setText("Window overlap fraction")
        # Create spinbox
        self.window_overlap_fraction_spinbox = Power2SteppedSpinBox(self)
        self.window_overlap_fraction_spinbox.setObjectName("window_overlap_fraction_spinbox")
        self.window_overlap_fraction_spinbox.setRange(1, 64)
        # Create slider
        self.window_overlap_fraction_slider = Power2SteppedSlider(Qt.Horizontal, self)
        self.window_overlap_fraction_slider.setObjectName("window_overlap_fraction_slider")
        self.window_overlap_fraction_slider.setRange(1, 64)
        # Connect spinbox and slider together
        self.window_overlap_fraction_spinbox.valueChanged.connect(self.window_overlap_fraction_slider.setValue)
        self.window_overlap_fraction_slider.valueChanged.connect(self.window_overlap_fraction_spinbox.setValue)
        # Set values
        self.window_overlap_fraction_spinbox.setValue(self.window_overlap_fraction)
        self.window_overlap_fraction_slider.setValue(self.window_overlap_fraction)
        # Update screen on change
        self.window_overlap_fraction_slider.valueChanged.connect(self.sonogram_plot.update_attributes)
        self.window_overlap_fraction_spinbox.valueChanged.connect(self.sonogram_plot.update_attributes)

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

        #------------Matplotlib window controls---------
        # Create button
        self.convert_to_contour_btn = QPushButton("Convert to contour plot", self)
        self.convert_to_contour_btn.resize(self.convert_to_contour_btn.sizeHint())
        self.convert_to_contour_btn.clicked.connect(self.open_contour_plot)

        #------------Layout------------
        # Sonogram controls:
        self.sonogram_controls_label = QLabel(self)
        self.sonogram_controls_label.setText("<b>Sonogram controls</b>")

        sonogram_controls = QGridLayout()
        sonogram_controls.addWidget(self.sonogram_controls_label, 0, 0)
        sonogram_controls.addWidget(self.window_width_label, 1, 0)
        sonogram_controls.addWidget(self.window_width_spinbox, 1, 1)
        sonogram_controls.addWidget(self.window_width_slider, 1, 2)
        sonogram_controls.addWidget(self.window_overlap_fraction_label, 2, 0)
        sonogram_controls.addWidget(self.window_overlap_fraction_spinbox, 2, 1)
        sonogram_controls.addWidget(self.window_overlap_fraction_slider, 2, 2)


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
        plot_controls.addWidget(self.convert_to_contour_btn, 4, 0, 1, 2)


        vbox = QVBoxLayout()
        hbox = QHBoxLayout()

        hbox.addWidget(self.sonogram_plot)
        hbox.addLayout(plot_controls)

        vbox.addLayout(hbox)
        vbox.addLayout(sonogram_controls)

        self.setLayout(vbox)
        self.setWindowTitle('Sonogram')
        self.show()

    def plot(self, sig):
        self.sonogram_plot.update_plot(sig)

    def open_contour_plot(self):
        if hasattr(self, 'contour_plot'):
            self.contour_plot.close()

        self.contour_plot = SonogramContourWidget(self)
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
    sonogram = SonogramWidget()
    sonogram.plot(sig)

    sys.exit(app.exec_())

