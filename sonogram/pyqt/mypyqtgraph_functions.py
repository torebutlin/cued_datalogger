import numpy as np

from matplotlib.cm import get_cmap
from matplotlib.colors import Colormap

import pyqtgraph as pg
from pyqtgraph import PlotWidget
from pyqtgraph.Qt import QtGui

from PyQt5.QtGui import QGraphicsItemGroup

class SimpleColormap(Colormap):
    def __init__(self, name):
        self.cmap = get_cmap(name)
        super().__init__(name)
    
    def to_rgb(self, x):
        return np.asarray(self.cmap(x)) * 255


class ContourMapPlot(PlotWidget):
    def __init__(self, x, y, Z, num_contours=32, contour_spacing=1e-3, cmap="jet"):
        self.x = x
        self.y = y
        self.Z = Z
        self.num_contours = num_contours
        self.contour_spacing = contour_spacing
        self.cmap = SimpleColormap(cmap)
        
        self.update_scale_fact()
        
        super().__init__()
        # Calculate the initial contours
        self.update_map()
                 
    def update_map(self, show_contours=False):
        # Set axes scaling
        x_axis = self.getAxis('bottom')
        y_axis = self.getAxis('left')
        
        x_axis.setScale(self.x_scale_fact)
        y_axis.setScale(self.y_scale_fact)
        
        self.autoRange()
        
        # Clear the current screen
        self.clear()
        
        self.z_img = pg.ImageItem(self.Z.transpose())
        
        if show_contours:
            for i in np.linspace(0, 1, self.num_contours):
                level = i*self.contour_spacing
                # Create the contour with a given colour
                contour = pg.IsocurveItem(pen=self.cmap.to_rgb(i))
                # Set the data for the contour at the specified level
                contour.setData(self.z_img.image, level=level)
                # Add it to the plot
                self.addItem(contour)
        else:
            #self.z_img.setTransform(self.samples_to_units)
            self.z_img.setLookupTable(self.cmap.to_rgb(np.arange(256)))
            self.addItem(self.z_img)

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
