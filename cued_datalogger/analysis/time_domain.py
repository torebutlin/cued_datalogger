from cued_datalogger.api.pyqtgraph_extensions import InteractivePlotWidget
from cued_datalogger.api.toolbox import Toolbox

from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton
from PyQt5.QtCore import pyqtSignal

import pyqtgraph as pg
import numpy as np
from numpy.fft import rfft

class TimeDomainWidget(InteractivePlotWidget):
    """
    The TimeDomainWidget is the main display widget for everything in
    the time domain.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.channels = []

    def set_selected_channels(self, selected_channels):
        """Update which channels are plotted"""
        # If no channel list is given
        if not selected_channels:
            self.channels = []
        else:
            self.channels = selected_channels
        self.update_plot()

    def update_plot(self):
        self.clear()
        for channel in self.channels:
            time_series = channel.data("time_series")
            if not time_series.shape[0] == 0:
                self.plot(channel.data("time"),
                          time_series,
                          pen=channel.colour)


class TimeToolbox(Toolbox):
    """Toolbox containing the Time Domain controls."""

    sig_convert_to_sonogram = pyqtSignal()
    sig_convert_to_fft = pyqtSignal()
    sig_converted_FFT = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.parent = parent
        self.cs = None

        self.init_ui()

    def init_ui(self):
        self.convert_tab = QWidget(self)
        convert_tab_layout = QGridLayout()

        self.fft_btn = QPushButton("Convert to FFT")
        self.fft_btn.clicked.connect(self.compute_fft)
        convert_tab_layout.addWidget(self.fft_btn, 0, 0)

        self.sonogram_btn = QPushButton("Convert to Sonogram")
        self.sonogram_btn.clicked.connect(self.sig_convert_to_sonogram.emit)
        convert_tab_layout.addWidget(self.sonogram_btn, 1, 0)

        convert_tab_layout.setRowStretch(2, 1)

        self.convert_tab.setLayout(convert_tab_layout)

        self.addTab(self.convert_tab, "Conversion")

    def set_channel_set(self,cs):
        self.cs = cs

    def compute_fft(self):
        # If no spectrum exists, calculate one
        print("Calculating spectrum...")
        for i in range(len(self.cs)):
            time_sig = self.cs.channel_data(i,"time_series")
            if not time_sig.shape[0] == 0:
                #window = np.hanning(len(time_sig))
                cycle=np.linspace(0,2*np.pi,time_sig.shape[0])
                window=1-np.cos(cycle);
                spectrum = rfft(time_sig * window)
                if not self.cs.channels[i].is_dataset("spectrum"):
                    self.cs.add_channel_dataset(i, "spectrum", spectrum)
                else:
                    self.cs.set_channel_data(i, "spectrum", spectrum)
            else:
                print('No Time Signal')

        print("Done.")
        self.sig_converted_FFT.emit()

