from PyQt5.QtCore import pyqtSignal, Qt
import numpy as np

# ------------------------------------------------------
# Basic PyQt Widgets
# ------------------------------------------------------
from PyQt5.QtWidgets import QSlider, QSpinBox

class Power2SteppedSlider(QSlider):
    """A QSlider that increments in powers of 2 when moved"""
    
    # Create custom signal, overriding pre-existing valueChanged signal
    valueChanged = pyqtSignal(int)
      
    def __init__(self, orientation, parent=None):

        QSlider.__init__(self, orientation)
        
        # Update value whenever slider is moved
        self.sliderMoved.connect(self.round_to_power_2)
            
    def round_to_power_2(self, value):
        # Round value to nearest power of 2
        n = np.round(np.log(value)/np.log(2))
        self.setValue(2**n)
        self.valueChanged.emit(2**n)
        
        
class Power2SteppedSpinBox(QSpinBox):
    """A QSpinBox that increments in powers of 2 when the value is updated""" 
    
    # Create custom signal, overriding pre-existing valueChanged signal
    valueChanged = pyqtSignal(int)
     
    def __init__(self, parent=None):

        QSpinBox.__init__(self)
        
        # Update data when focus is lost or enter pressed
        self.editingFinished.connect(self.round_to_power_2)
        
        # Lose focus if clicked elsewhere
        self.setFocusPolicy(Qt.ClickFocus)
        parent.setFocusPolicy(Qt.ClickFocus)
               
    def round_to_power_2(self):
        # Round value to nearest power of 2
        n = np.round(np.log(self.value())/np.log(2))
        self.setValue(2**n)
        self.valueChanged.emit(2**n)
    
    def mouseReleaseEvent(self, event):
        # Lose focus if mouse released
        self.clearFocus()

# ------------------------------------------------------
# PyQtGraph Widgets
# ------------------------------------------------------
from matplotlib.cm import get_cmap
from matplotlib.colors import Colormap

from pyqtgraph import PlotWidget, ImageItem


class SimpleColormap(Colormap):
    def __init__(self, name):
        self.cmap = get_cmap(name)
        super().__init__(name)
    
    def to_rgb(self, x):
        return np.asarray(self.cmap(x)) * 255


class ColorMapPlotWidget(PlotWidget):
    """A PlotWidget optimised for plotting color(heat) maps"""
    def __init__(self, parent=None, cmap="jet"):
        self.cmap = SimpleColormap(cmap)
        self.num_contours = 5
        self.contour_spacing_dB = 5
        self.parent = parent
        super().__init__(parent=self.parent)
        
    def plot_colormap(self, x, y, z, num_contours=5, contour_spacing_dB=5):
        self.x = x
        self.y = y
        self.z = z
        
        self.num_contours = num_contours
        self.contour_spacing_dB = contour_spacing_dB
        self.update_lowest_contour()
        
        # Set up axes:
        x_axis = self.getAxis('bottom')
        y_axis = self.getAxis('left')

        self.x_scale_fact = self.get_scale_fact(x)
        self.y_scale_fact = self.get_scale_fact(y)
        
        x_axis.setScale(self.x_scale_fact)
        y_axis.setScale(self.y_scale_fact)
        
        #self.autoRange()
        
        self.z_img = ImageItem(z.transpose())
        self.z_img.setLookupTable(self.cmap.to_rgb(np.arange(256)))
        self.z_img.setLevels([self.lowest_contour, self.highest_contour])
        self.addItem(self.z_img)

    def get_scale_fact(self, var):
        return var.max() / var.size
    
    def update_lowest_contour(self):
        """Find the lowest contour to plot"""
        self.lowest_contour = self.z.max() - (self.num_contours * self.contour_spacing_dB)
        self.highest_contour = self.z.max()
        
# -----------------------------------------
# Matplotlib widgets
# -----------------------------------------
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtWidgets import QSizePolicy


class MatplotlibCanvas(FigureCanvas):
    def __init__(self, suptitle=None):
        matplotlib.use('Qt5Agg')  
        matplotlib.rcParams['toolbar'] = 'None'

        fig = Figure()
        fig.suptitle(suptitle)
        self.axes = fig.add_subplot(111)

        self.init_plot()
        
        FigureCanvas.__init__(self, fig)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def init_plot(self):
        pass
    
    def draw_plot(self):
        pass
    
    def update_plot(self):
        pass