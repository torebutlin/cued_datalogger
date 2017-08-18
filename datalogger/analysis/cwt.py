import numpy as np

from scipy.signal import ricker, cwt

from datalogger.api.pyqt_widgets import MatplotlibCanvas

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QSlider, QLabel, QSpinBox, QHBoxLayout, QGridLayout, QComboBox

from PyQt5.QtCore import Qt

import sys

#--------------------------------
from scipy.signal import gausspulse
#import matplotlib.pyplot as plt

t = np.linspace(-1, 1, 200, endpoint=False)
sig  = np.cos(2 * np.pi * 7 * t) + gausspulse(t - 0.4, fc=2)
widths = np.arange(1, 31)
"""
cwt_result = cwt(sig, ricker, widths)

T, W = np.meshgrid(t, widths)

plt.figure()
plt.contour(T, W, cwt_result)
plt.show()
#----------------------------------
"""


class CWTPlotWidget(MatplotlibCanvas):
    """A MatplotlibCanvas widget displaying the CWT plot"""
    
    def __init__(self, sig, t, widths, wavelet=ricker, plot_type="Colourmap",
                 num_contours=5, contour_spacing_dB=5):
        self.sig = sig
        self.t = t
        self.widths = widths
        self.wavelet = wavelet
        self.plot_type = plot_type
        self.num_contours = num_contours
        self.contour_spacing_dB = contour_spacing_dB
        
        MatplotlibCanvas.__init__(self, "Continuous Wavelet Transform")
        
        self.calculate_cwt()
        self.draw_plot()
    
    def draw_plot(self):
        """Redraw the CWT on the canvas"""
        
        self.axes.clear()
        
        if self.plot_type == "Contour":
            
            self.update_contour_sequence()
            
            self.axes.contour(self.T, self.W, self.cwt_result, self.contour_sequence)
            
            self.axes.set_xlabel('Time (s)')
            self.axes.set_ylabel('Wavelet width (?)')
            
            self.axes.set_xlim(self.t.min(), self.t.max())
            self.axes.set_ylim(self.widths.min(), self.widths.max())
            
        elif self.plot_type == "Surface":
            pass
        
        elif self.plot_type == "Colourmap":
            
            self.update_contour_sequence()
            
            self.axes.pcolormesh(self.T, self.W, self.cwt_result, vmin=self.contour_sequence[0])
            
            self.axes.set_xlabel('Time (s)')
            self.axes.set_ylabel('Wavelet width (?)')
            
            self.axes.set_xlim(self.t.min(), self.t.max())
            self.axes.set_ylim(self.widths.min(), self.widths.max())
            
        else:
            pass
        
        self.draw()
        
    def update_attributes(self, value):
        """A slot for updating the attributes when input widgets are adjusted"""
        
        # What sent the signal?
        sender_name = self.sender().objectName()
        
        if sender_name == "plot_type_combobox":
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
        self.calculate_cwt()
        self.draw_plot()
    
    def calculate_cwt(self):
        """Recalculate the CWT"""
        self.cwt_result = cwt(self.sig, self.wavelet, self.widths)

        self.T, self.W = np.meshgrid(self.t, self.widths)

    
    def update_contour_sequence(self):
        """Update the array which says where to plot contours, how many etc"""
        # Create a vector with the right spacing from min to max value
        self.contour_sequence = np.arange(self.cwt_result.min(), self.cwt_result.max(),
                                          self.contour_spacing_dB)
        # Take the appropriate number of contours
        self.contour_sequence = self.contour_sequence[-self.num_contours:]


class CWTWidget(QWidget):
    def __init__(self, sig, t, widths=np.arange(1, 31), parent=None):
        self.sig = sig
        self.t = t
        self.widths = widths
               
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        # Add a cwt plot
        self.cwt_plot = CWTPlotWidget(self.sig, self.t, self.widths)
              
        #------------Plot type controls------------
        self.plot_type_label = QLabel(self)
        self.plot_type_label.setText("Plot type")
        # Create combobox
        self.plot_type_combobox = QComboBox(self)
        self.plot_type_combobox.addItems(["Colourmap", "Contour", "Surface"])
        self.plot_type_combobox.setObjectName("plot_type_combobox")
        # Update on change
        self.plot_type_combobox.activated[str].connect(self.cwt_plot.update_attributes)        
        
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
        self.contour_spacing_spinbox.setValue(self.cwt_plot.contour_spacing_dB)
        self.contour_spacing_slider.setValue(self.cwt_plot.contour_spacing_dB)
        # Update screen on change
        self.contour_spacing_slider.valueChanged.connect(self.cwt_plot.update_attributes)
        self.contour_spacing_spinbox.valueChanged.connect(self.cwt_plot.update_attributes)
        
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
        self.num_contours_spinbox.setValue(self.cwt_plot.num_contours)
        self.num_contours_slider.setValue(self.cwt_plot.num_contours)
        # Update screen on change
        self.num_contours_slider.valueChanged.connect(self.cwt_plot.update_attributes)
        self.num_contours_spinbox.valueChanged.connect(self.cwt_plot.update_attributes)
        
        #------------Layout------------
        # CWT controls:
        self.cwt_controls_label = QLabel(self)
        self.cwt_controls_label.setText("<b>CWT controls</b>")
        
        cwt_controls = QGridLayout()
        cwt_controls.addWidget(self.cwt_controls_label, 0, 0)
        
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
        
        hbox.addWidget(self.cwt_plot)
        hbox.addLayout(plot_controls)
        
        vbox.addLayout(hbox)
        vbox.addLayout(cwt_controls)

        self.setLayout(vbox)
        self.setWindowTitle('CWT')
        self.show()

if __name__ == '__main__':  
    app = 0
    
    app = QApplication(sys.argv)
    cwt_w = CWTWidget(sig, t)
        
    sys.exit(app.exec_())  
    