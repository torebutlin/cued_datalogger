from datalogger.api.pyqtgraph_extensions import InteractivePlotWidget
from datalogger.api.toolbox import Toolbox

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal

import pyqtgraph as pg

class TimeDomainWidget(InteractivePlotWidget):
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
            self.plot(channel.get_data("time"),
                      channel.get_data("time_series"),
                      pen=pg.mkPen(channel.colour))


class TimeToolbox(Toolbox):
    """Toolbox containing the Time Domain controls"""
    
    sig_convert_to_sonogram = pyqtSignal()
    sig_convert_to_fft = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.parent = parent
        
        self.init_ui()
    
    def init_ui(self):
        self.convert_tab = QWidget(self)
        convert_tab_layout = QVBoxLayout()

        self.fft_btn = QPushButton("Convert to FFT")
        self.fft_btn.clicked.connect(self.sig_convert_to_fft.emit)
        convert_tab_layout.addWidget(self.fft_btn)
      
        self.sonogram_btn = QPushButton("Convert to Sonogram")
        self.sonogram_btn.clicked.connect(self.sig_convert_to_sonogram.emit)
        convert_tab_layout.addWidget(self.sonogram_btn)
        
        self.convert_tab.setLayout(convert_tab_layout)
        
        self.addTab(self.convert_tab, "Conversion")
