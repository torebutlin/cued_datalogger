from cued_datalogger.api.pyqtgraph_extensions import InteractivePlotWidget
from cued_datalogger.api.toolbox import Toolbox

from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton
from PyQt5.QtCore import pyqtSignal


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
        self.channels = []

        if selected_channels:
            self.channels = selected_channels

        self.update_plot()

    def update_plot(self):
        self.clear()
        for channel in self.channels:
            if channel.is_dataset("time_series"):
                self.plot(channel.data("time"),
                          channel.data("time_series"),
                          pen=channel.colour)


class TimeToolbox(Toolbox):
    """
    Toolbox containing the Time Domain controls.

    Attributes
    ----------
    sig_convert_to_sonogram : pyqtSignal
        Signal emitted when the 'Convert to sonogram' button is clicked.
    sig_convert_to_fft : pyqtSignal
        Signal emitted when the 'Convert to frequency spectrum' button is
        clicked.

    """
    sig_convert_to_sonogram = pyqtSignal()
    sig_convert_to_fft = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        self.convert_tab = QWidget(self)
        convert_tab_layout = QGridLayout()

        self.fft_btn = QPushButton("Convert to frequency spectrum")
        self.fft_btn.clicked.connect(self.sig_convert_to_fft.emit)
        convert_tab_layout.addWidget(self.fft_btn, 0, 0)

        self.sonogram_btn = QPushButton("Convert to sonogram")
        self.sonogram_btn.clicked.connect(self.sig_convert_to_sonogram.emit)
        convert_tab_layout.addWidget(self.sonogram_btn, 1, 0)

        convert_tab_layout.setRowStretch(2, 1)

        self.convert_tab.setLayout(convert_tab_layout)

        self.addTab(self.convert_tab, "Conversion")
