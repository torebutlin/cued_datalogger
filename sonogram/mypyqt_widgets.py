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

import pyqtgraph as pg
from pyqtgraph import PlotWidget
from pyqtgraph.Qt import QtGui


class SimpleColormap(Colormap):
    def __init__(self, name):
        self.cmap = get_cmap(name)
        super().__init__(name)
    
    def to_rgb(self, x):
        return np.asarray(self.cmap(x)) * 255


class ColorMapPlot(PlotWidget):
    def __init__(self, x, y, z, num_contours, contour_spacing_dB, cmap="jet"):
        self.x = x
        self.y = y
        self.z = z
        self.num_contours = num_contours
        self.contour_spacing_dB = contour_spacing_dB
        self.cmap = SimpleColormap(cmap)
        self.samples_to_units = None
        
        super().__init__()
        
        # Draw the initial plot
        self.update()
                 
    def update(self):
        # Set the axes limits to display 1% more than the maximum value
        self.setXRange(0, self.x.max() * 1.01)
        self.setYRange(0, self.y.max() * 1.01)

        # Update the scale factor
        self.update_scale_fact()

        # Create the new colour plot
        colorplot = pg.ImageItem(self.z.transpose())
        # Transform it
        colorplot.setTransform(self.samples_to_units)
        # Set the colours
        colorplot.setLookupTable(self.cmap.to_rgb(np.arange(256)))
        
        # Clear the current screen
        self.clear()
        # Show the colour map in the PlotWidget
        self.addItem(colorplot)

    def update_scale_fact(self):
        # We need to convert from x and y being in 'samples' to being in 'units'.
        # Currently the values of Z will just be plotted on axes where the scale
        # is the (i, j) position of the value in Z.
        # We want to plot them on axes where the scale is x, y.
        # To do this we use a QTransform matrix
        self.samples_to_units = QtGui.QTransform()
        # Scale factor to map the largest sample number to the largest unit
        self.x_scale_fact = self.x.max() / self.x.size
        self.y_scale_fact = self.y.max() / self.y.size
        # Set the values in the transformation matrix
        self.samples_to_units.scale(self.x_scale_fact, self.y_scale_fact)