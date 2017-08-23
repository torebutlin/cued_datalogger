from datalogger.api.pyqtgraph_extensions import InteractivePlotWidget
from datalogger.api.toolbox import Toolbox
from datalogger.api.numpy_extensions import to_dB

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QComboBox
from PyQt5.QtCore import pyqtSignal

import scipy.fftpack
import numpy as np
import pyqtgraph as pg

class FrequencyDomainWidget(InteractivePlotWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.plot_types = ['Linear Magnitude',
                           'Log Magnitude',
                           'Phase',
                           'Real Part',
                           'Imaginary Part',
                           'Nyquist']
        self.current_plot_type = self.plot_types[0]
                
        self.current_plot = "spectrum"
    
    def set_selected_channels(self, selected_channels):
        """Update which channels are plotted"""
        # If no channel list is given
        if not selected_channels:
            self.channels = []
        else:
            self.channels = selected_channels
        
        self.update_plot()
    
    def set_plot_type(self, index):
        self.current_plot_type = self.plot_types[index]
        self.update_plot()
    
    def update_plot(self):
        self.clear()
 
        for channel in self.channels:
            if self.current_plot == "spectrum":
                if not channel.is_dataset(self.current_plot):
                    print('No Fourier Transform to plot')   
                    continue
                '''
                # If no spectrum exists, calculate one
                print("Recalculating spectrum...")
                units = channel.get_units("time_series")
                #spectrum = scipy.fftpack.rfft(channel.get_data("time_series"))
                spectrum = np.fft.rfft(channel.get_data("time_series"))
                if not channel.is_dataset(self.current_plot):
                    channel.add_dataset(self.current_plot, units, spectrum)
                else:
                    channel.set_data(self.current_plot, spectrum)
                
                print("Done.")
                '''
            elif self.current_plot == "TF":
                if not channel.is_dataset(self.current_plot):
                    print('No Transfer Function to plot')   
                    continue
                
            # Plot
            if self.current_plot_type == 'Linear Magnitude':
                print("Plotting Linear Magnitude.")
                self.plot(channel.get_data("frequency"), 
                          np.abs(channel.get_data(self.current_plot)),
                          pen=pg.mkPen(channel.colour))
                
            elif self.current_plot_type == 'Log Magnitude':
                print("Plotting Log Magnitude.")
                self.plot(channel.get_data("frequency"),
                          to_dB(np.abs(channel.get_data(self.current_plot))),
                          pen=pg.mkPen(channel.colour))
                
            elif self.current_plot_type == 'Phase':
                print("Plotting Phase.")
                self.plot(channel.get_data("frequency"), 
                          np.angle(channel.get_data(self.current_plot),deg=True),
                          pen=pg.mkPen(channel.colour))
                
            elif self.current_plot_type == 'Real Part':
                print("Plotting Real Part.")
                self.plot(channel.get_data("frequency"),
                          np.real(channel.get_data(self.current_plot)),
                          pen=pg.mkPen(channel.colour))
                
            elif self.current_plot_type == 'Imaginary Part':
                print("Plotting Imaginary Part.")
                self.plot(channel.get_data("frequency"), 
                          np.imag(channel.get_data(self.current_plot)),
                          pen=pg.mkPen(channel.colour))
                
            elif self.current_plot_type == 'Nyquist':
                print("Plotting Nyquist.")
                self.plot(np.real(channel.get_data(self.current_plot)), 
                          np.imag(channel.get_data(self.current_plot)),
                          pen=pg.mkPen(channel.colour))

            
class FrequencyToolbox(Toolbox):
    """Toolbox containing the Frequency Domain controls"""
    sig_convert_to_TF = pyqtSignal()
    sig_convert_to_circle_fit = pyqtSignal()
    sig_plot_type_changed = pyqtSignal(int)
    sig_view_type_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.parent = parent
        
        self.init_ui()
    
    def init_ui(self):
        # # Plot options tab
        self.plot_options_tab = QWidget(self)
        plot_options_tab_layout = QVBoxLayout()
        self.view_type_combobox = QComboBox(self)
        self.view_type_combobox.addItems(['Fourier Transform','Transfer Function'])
        self.view_type_combobox.currentIndexChanged[str].connect(self.sig_view_type_changed.emit)
        plot_options_tab_layout.addWidget(self.view_type_combobox)
        self.plot_type_combobox = QComboBox(self.plot_options_tab)
        self.plot_type_combobox.addItems(['Linear Magnitude',
                                          'Log Magnitude',
                                          'Phase',
                                          'Real Part',
                                          'Imaginary Part',
                                          'Nyquist'])
    
        self.plot_type_combobox.setCurrentIndex(0)
        self.plot_type_combobox.currentIndexChanged.connect(self.sig_plot_type_changed.emit)
        plot_options_tab_layout.addWidget(self.plot_type_combobox)
        
        self.plot_options_tab.setLayout(plot_options_tab_layout)
        
        self.addTab(self.plot_options_tab, "Plot Options")
        # # Conversion tab
        self.convert_tab = QWidget(self)
        convert_tab_layout = QVBoxLayout()
        
        self.view_tf_btn = QPushButton("Convert FFT to TF")
        self.convert_tab.setLayout(convert_tab_layout)
        #self.view_tf_btn.clicked.connect(self.sig_convert_to_TF.emit)
        convert_tab_layout.addWidget(self.view_tf_btn)        
        
        self.circle_fit_btn = QPushButton("Convert to Circle Fit")
        self.circle_fit_btn.clicked.connect(self.sig_convert_to_circle_fit.emit)
        convert_tab_layout.addWidget(self.circle_fit_btn)

        self.addTab(self.convert_tab, "Conversion")
        
    def set_view_type(self,vtype):
        self.view_type_combobox.setCurrentText(vtype)
        
def compute_autospec(fft_data):
    return(fft_data * np.conjugate(fft_data))

def compute_crossspec(in_fft_data,out_fft_data):
    return(np.conjugate(in_fft_data) * out_fft_data)

def compute_transfer_function(autospec_in,autospec_out,crossspec):
   
    transfer_func = (autospec_out/crossspec)
    coherence = ((crossspec * np.conjugate(crossspec))/(autospec_in*autospec_out))
    
    return(transfer_func,coherence)
